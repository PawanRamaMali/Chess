from Chessnut import Game
import random
import time

# Enhanced piece values matching the C++ implementation
PIECE_VALUES = {
    'P': 100,  'N': 320,  'B': 330,
    'R': 500,  'Q': 900,  'K': 20000,
    'p': -100, 'n': -320, 'b': -330,
    'r': -500, 'q': -900, 'k': -20000,
    ' ': 0
}

# Position tables from C++ implementation
PIECE_TABLES = {
    'P': [  # Pawn
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [  # Knight
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
}

def count_pieces(board):
    """Fast piece counting using direct board access"""
    queens = major_pieces = 0
    for i in range(64):
        piece = board.get_piece(i)
        if piece.upper() == 'Q':
            queens += 1
        elif piece.upper() in 'RBN':
            major_pieces += 1
    return queens, major_pieces

def evaluate_move(board, move):
    """Fast move evaluation inspired by C++ implementation"""
    score = 0
    from_sq = Game.xy2i(move[0:2])
    to_sq = Game.xy2i(move[2:4])
    moving_piece = board.get_piece(from_sq)
    captured_piece = board.get_piece(to_sq)
    
    # Material and capture evaluation
    if captured_piece != ' ':
        score += PIECE_VALUES[captured_piece]
        # Bonus for favorable trades
        if abs(PIECE_VALUES[moving_piece]) < abs(PIECE_VALUES[captured_piece]):
            score += 50
    
    # Position scoring from tables
    to_file, to_rank = to_sq % 8, to_sq // 8
    piece_type = moving_piece.upper()
    if piece_type in PIECE_TABLES:
        position_value = PIECE_TABLES[piece_type][to_rank * 8 + to_file]
        score += position_value if moving_piece.isupper() else -position_value
    
    # Center control bonus (e4, d4, e5, d5)
    if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
        score += 10
        if 3 <= to_file <= 4 and 3 <= to_rank <= 4:
            score += 10
    
    # Promotion bonus
    if len(move) > 4 and move[4] == 'q':
        score += 800
        
    return score

def detect_checkmate_threat(game, move, max_depth=2):
    """Look ahead for checkmate threats"""
    if max_depth == 0:
        return False
        
    g = Game(game.fen)
    g.apply_move(move)
    
    # Immediate checkmate
    if g.status == Game.CHECKMATE:
        return True
    
    # Check forcing moves
    if g.status == Game.CHECK:
        defender_moves = list(g.get_moves())
        if not defender_moves:
            return True
            
        # Look for forced mate
        all_lead_to_mate = True
        for defense in defender_moves[:3]:  # Check first few defensive moves
            g2 = Game(g.fen)
            g2.apply_move(defense)
            if g2.status != Game.CHECKMATE:
                all_lead_to_mate = False
                break
        return all_lead_to_mate
        
    return False

def evaluate_position(board, moves):
    """Complete position evaluation"""
    score = 0
    queens, pieces = count_pieces(board)
    is_endgame = queens == 0 or pieces <= 6
    
    # Material evaluation
    for i in range(64):
        piece = board.get_piece(i)
        if piece != ' ':
            score += PIECE_VALUES[piece]
    
    # Positional evaluation for first few moves
    for move in moves[:5]:
        move_score = evaluate_move(board, move)
        if move[0].isupper():  # White's moves
            score += move_score
        else:  # Black's moves
            score -= move_score
            
    # Endgame adjustments
    if is_endgame:
        for i in range(64):
            piece = board.get_piece(i)
            if piece.upper() == 'K':
                rank, file = i // 8, i % 8
                center_dist = abs(3.5 - file) + abs(3.5 - rank)
                if piece.isupper():
                    score += (4 - center_dist) * 10
                else:
                    score -= (4 - center_dist) * 10
    
    return score

def alpha_beta(game, depth, alpha, beta, maximizing, start_time, max_time=0.95):
    """Alpha-beta search with fast evaluation"""
    if time.time() - start_time > max_time:
        return None, evaluate_position(game.board, game.get_moves())
    
    if depth == 0:
        return None, evaluate_position(game.board, game.get_moves())
    
    moves = list(game.get_moves())
    if not moves:
        if game.status == Game.CHECKMATE:
            return None, -99999 if maximizing else 99999
        return None, 0
    
    # Quick sort moves by immediate value
    moves.sort(key=lambda m: evaluate_move(game.board, m), reverse=True)
    
    best_move = moves[0]
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            g = Game(game.fen)
            g.apply_move(move)
            
            # Quick checkmate detection
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
    """Enhanced chess bot with fast evaluation"""
    try:
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
        
        # Check for immediate checkmate
        for move in moves[:5]:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        # Look for checkmate threats
        for move in moves[:8]:
            if detect_checkmate_threat(game, move):
                return move
        
        # Main search
        start_time = time.time()
        best_move = moves[0]
        
        # Iterative deepening with move ordering
        for depth in range(1, 5):
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