from Chessnut import Game
import random
import time

PIECE_VALUES = {
    'P': 100,  'N': 320,  'B': 330,
    'R': 500,  'Q': 900,  'K': 20000,
    'p': -100, 'n': -320, 'b': -330,
    'r': -500, 'q': -900, 'k': -20000,
    ' ': 0
}

# Endgame piece-square tables
ENDGAME_PST = {
    'K': [  # King becomes more active in endgame
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 20, 20, 20, 20, 10,-10,
        -10, 10, 20, 30, 30, 20, 10,-10,
        -10, 10, 20, 30, 30, 20, 10,-10,
        -10, 10, 20, 20, 20, 20, 10,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'P': [  # Pawns more valuable when advanced in endgame
        0,  0,  0,  0,  0,  0,  0,  0,
        80, 80, 80, 80, 80, 80, 80, 80,
        50, 50, 50, 50, 50, 50, 50, 50,
        30, 30, 30, 40, 40, 30, 30, 30,
        20, 20, 20, 30, 30, 20, 20, 20,
        10, 10, 10, 15, 15, 10, 10, 10,
        5,  5,  5, 10, 10,  5,  5,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
}

def get_material_config(board):
    """Get material configuration for endgame detection"""
    pieces = {'P': 0, 'N': 0, 'B': 0, 'R': 0, 'Q': 0,
             'p': 0, 'n': 0, 'b': 0, 'r': 0, 'q': 0}
    
    for i in range(64):
        piece = board.get_piece(i)
        if piece != ' ':
            pieces[piece] += 1
            
    return pieces

def is_endgame(material_config):
    """Detect various endgame types"""
    # Convert piece counts to score for each side
    white_score = (material_config['Q'] * 9 + 
                  material_config['R'] * 5 +
                  material_config['B'] * 3 +
                  material_config['N'] * 3)
    
    black_score = (material_config['q'] * 9 +
                  material_config['r'] * 5 +
                  material_config['b'] * 3 +
                  material_config['n'] * 3)
    
    return white_score <= 13 and black_score <= 13

def manhattan_distance(sq1, sq2):
    """Calculate Manhattan distance between two squares"""
    rank1, file1 = sq1 // 8, sq1 % 8
    rank2, file2 = sq2 // 8, sq2 % 8
    return abs(rank1 - rank2) + abs(file1 - file2)

def evaluate_endgame_specific(board, material_config):
    """Specific endgame evaluations"""
    score = 0
    
    # Find kings
    white_king = black_king = -1
    for i in range(64):
        piece = board.get_piece(i)
        if piece == 'K':
            white_king = i
        elif piece == 'k':
            black_king = i
    
    if white_king == -1 or black_king == -1:
        return 0
        
    # King and Pawn endgames
    if sum(material_config[p] for p in 'QRBNqrbn') == 0:
        # Drive enemy king to the edge
        white_king_rank, white_king_file = white_king // 8, white_king % 8
        black_king_rank, black_king_file = black_king // 8, black_king % 8
        
        # Centralization bonus for winning side
        white_center_dist = min(white_king_file, 7-white_king_file) + min(white_king_rank, 7-white_king_rank)
        black_center_dist = min(black_king_file, 7-black_king_file) + min(black_king_rank, 7-black_king_rank)
        
        if material_config['P'] > material_config['p']:
            score += (14 - white_center_dist * 2) * 10  # Bonus for centralizing king
            score += black_center_dist * 10  # Push enemy king to edge
        elif material_config['p'] > material_config['P']:
            score -= (14 - black_center_dist * 2) * 10
            score -= white_center_dist * 10
    
    # King and Queen vs King
    if material_config['Q'] == 1 and sum(material_config[p] for p in 'RBNPrbnp') == 0:
        score += 500  # Base bonus for having queen
        score += (14 - manhattan_distance(white_king, black_king)) * 30  # Drive kings together
    elif material_config['q'] == 1 and sum(material_config[p] for p in 'RBNPrbnp') == 0:
        score -= 500
        score -= (14 - manhattan_distance(white_king, black_king)) * 30
    
    # Rook endgames
    if material_config['R'] > 0 or material_config['r'] > 0:
        # Bonus for rooks on 7th rank
        for i in range(8):
            piece = board.get_piece(1 * 8 + i)  # 7th rank for white
            if piece == 'R':
                score += 50
            piece = board.get_piece(6 * 8 + i)  # 2nd rank for black
            if piece == 'r':
                score -= 50
    
    # Bishop pair bonus
    if material_config['B'] >= 2:
        score += 50
    if material_config['b'] >= 2:
        score -= 50
    
    return score

def evaluate_passed_pawns(board, is_endgame):
    """Evaluate passed pawns, especially important in endgames"""
    score = 0
    
    for i in range(64):
        piece = board.get_piece(i)
        if piece.upper() != 'P':
            continue
            
        rank, file = i // 8, i % 8
        is_white = piece == 'P'
        
        # Check if pawn is passed
        passed = True
        enemy_pawn = 'p' if is_white else 'P'
        
        # Check files
        for check_file in [file-1, file, file+1]:
            if check_file < 0 or check_file > 7:
                continue
                
            # Check ranks in front of pawn
            ranks_to_check = range(rank-1, -1, -1) if is_white else range(rank+1, 8)
            for check_rank in ranks_to_check:
                if board.get_piece(check_rank * 8 + check_file) == enemy_pawn:
                    passed = False
                    break
        
        if passed:
            # Base score for passed pawn
            base_score = 50
            
            # Additional score based on rank
            rank_bonus = (7 - rank if is_white else rank) * 10
            
            # Endgame bonus
            if is_endgame:
                base_score *= 2
                rank_bonus *= 2
            
            score += (base_score + rank_bonus) * (1 if is_white else -1)
    
    return score

def evaluate_position(board, moves):
    """Enhanced position evaluation with endgame knowledge"""
    material_config = get_material_config(board)
    is_endgame_pos = is_endgame(material_config)
    score = 0
    
    # Basic material counting
    for piece, count in material_config.items():
        score += PIECE_VALUES[piece] * count
    
    # Endgame specific evaluation
    if is_endgame_pos:
        score += evaluate_endgame_specific(board, material_config)
        score += evaluate_passed_pawns(board, True)
    else:
        score += evaluate_passed_pawns(board, False)
    
    # Mobility evaluation
    score += len(moves) // 2
    
    return score

def alpha_beta(game, depth, alpha, beta, maximizing, start_time, max_time=0.95):
    """Alpha-beta search with endgame knowledge"""
    if time.time() - start_time > max_time:
        return None, evaluate_position(game.board, game.get_moves())
    
    if depth == 0:
        return None, evaluate_position(game.board, game.get_moves())
    
    moves = list(game.get_moves())
    if not moves:
        if game.status == Game.CHECKMATE:
            return None, -99999 if maximizing else 99999
        return None, 0
    
    material_config = get_material_config(game.board)
    is_endgame_pos = is_endgame(material_config)
    
    # Sort moves differently in endgame
    if is_endgame_pos:
        # Prioritize passed pawn advances and king centralization
        moves.sort(key=lambda m: (
            1000 if game.board.get_piece(Game.xy2i(m[0:2])).upper() == 'P' else 0
            + 500 if game.board.get_piece(Game.xy2i(m[0:2])).upper() == 'K' else 0
        ), reverse=True)
    else:
        # Normal move ordering
        moves.sort(key=lambda m: (
            1000 if game.board.get_piece(Game.xy2i(m[2:4])) != ' ' else 0
        ), reverse=True)
    
    best_move = moves[0]
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            g = Game(game.fen)
            g.apply_move(move)
            
            if g.status == Game.CHECKMATE:
                return move, 99999
            
            _, eval = alpha_beta(g, depth-1, alpha, beta, False, start_time, max_time)
            
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return best_move, max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            g = Game(game.fen)
            g.apply_move(move)
            
            if g.status == Game.CHECKMATE:
                return move, -99999
            
            _, eval = alpha_beta(g, depth-1, alpha, beta, True, start_time, max_time)
            
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return best_move, min_eval

def chess_bot(obs):
    """Chess bot with improved endgame play"""
    try:
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
        
        # Check for immediate checkmate
        for move in moves:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        start_time = time.time()
        best_move = moves[0]
        
        # Adjust search depth based on phase
        material_config = get_material_config(game.board)
        is_endgame_pos = is_endgame(material_config)
        max_depth = 5 if is_endgame_pos else 4  # Search deeper in endgame
        
        # Main search
        for depth in range(1, max_depth + 1):
            move, eval = alpha_beta(
                game=game,
                depth=depth,
                alpha=float('-inf'),
                beta=float('inf'),
                maximizing=True,
                start_time=start_time
            )
            
            if move is None:  # Time limit exceeded
                break
                
            best_move = move
            
            # Early exit on found checkmate
            if abs(eval) > 9000:
                break
        
        return best_move
        
    except Exception:
        return moves[0] if moves else None