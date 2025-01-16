from Chessnut import Game
import random
import time

PIECE_VALUES = {
    'P': 100,  'N': 320,  'B': 330,
    'R': 500,  'Q': 900,  'K': 20000
}

# Central squares for positional evaluation
CENTER_SQUARES = {
    'e4': 30, 'd4': 30, 'e5': 25, 'd5': 25,
    'c3': 15, 'f3': 15, 'c6': 15, 'f6': 15
}

def is_endgame(board):
    """Check if position is endgame based on material"""
    queens = major_pieces = 0
    for i in range(64):
        piece = board.get_piece(i)
        if piece.upper() == 'Q':
            queens += 1
        elif piece.upper() in 'RBN':
            major_pieces += 1
    return queens == 0 or (queens == 2 and major_pieces <= 2)

def evaluate_pawn_structure(board):
    """Evaluate pawn structure and chains"""
    score = 0
    pawns_white = [0] * 8
    pawns_black = [0] * 8
    
    # Map pawns to files
    for i in range(64):
        piece = board.get_piece(i)
        if piece.upper() == 'P':
            file = i % 8
            rank = i // 8
            if piece == 'P':
                pawns_white[file] += 1
                if rank >= 5:  # Advanced pawns
                    score += 10 * (rank - 4)
            else:
                pawns_black[file] += 1
                if rank <= 2:  # Advanced pawns
                    score -= 10 * (3 - rank)
    
    # Evaluate structure
    for file in range(8):
        # Doubled pawns
        if pawns_white[file] > 1:
            score -= 20 * (pawns_white[file] - 1)
        if pawns_black[file] > 1:
            score += 20 * (pawns_black[file] - 1)
        
        # Isolated pawns
        if pawns_white[file] > 0:
            if (file == 0 or pawns_white[file-1] == 0) and \
               (file == 7 or pawns_white[file+1] == 0):
                score -= 15
        if pawns_black[file] > 0:
            if (file == 0 or pawns_black[file-1] == 0) and \
               (file == 7 or pawns_black[file+1] == 0):
                score += 15
    
    return score

def evaluate_king_safety(board, king_sq, is_white, is_endgame):
    """Evaluate king safety depending on game phase"""
    score = 0
    rank, file = king_sq // 8, king_sq % 8
    
    if not is_endgame:
        # Pawn shield
        pawn = 'P' if is_white else 'p'
        shield_rank = rank - 1 if is_white else rank + 1
        if 0 <= shield_rank < 8:
            for f in range(max(0, file-1), min(8, file+2)):
                if board.get_piece(shield_rank * 8 + f) == pawn:
                    score += 15
    else:
        # King activity in endgame
        center_dist = abs(3.5 - file) + abs(3.5 - rank)
        score -= center_dist * 10  # Encourage centralization
    
    return score

def detect_tactics(board, move):
    """Detect basic tactical patterns"""
    score = 0
    from_sq = Game.xy2i(move[0:2])
    to_sq = Game.xy2i(move[2:4])
    moving_piece = board.get_piece(from_sq)
    target_piece = board.get_piece(to_sq)
    
    # Captures
    if target_piece != ' ':
        score += PIECE_VALUES.get(target_piece.upper(), 0)
        # Better trades
        if PIECE_VALUES.get(moving_piece.upper(), 0) < PIECE_VALUES.get(target_piece.upper(), 0):
            score += 50
    
    # Control of key squares
    square = f"{move[2]}{move[3]}"
    if square in CENTER_SQUARES:
        score += CENTER_SQUARES[square]
    
    return score

def evaluate_position(board, moves):
    """Complete position evaluation"""
    score = 0
    endgame = is_endgame(board)
    
    # Material and piece positioning
    for i in range(64):
        piece = board.get_piece(i)
        if piece != ' ':
            value = PIECE_VALUES.get(piece.upper(), 0)
            if piece.isupper():
                score += value
            else:
                score -= value
                
    # Pawn structure
    score += evaluate_pawn_structure(board)
    
    # King safety and piece activity
    for i in range(64):
        piece = board.get_piece(i)
        if piece.upper() == 'K':
            safety = evaluate_king_safety(board, i, piece.isupper(), endgame)
            score += safety if piece.isupper() else -safety
    
    # Tactics for available moves
    for move in moves[:5]:  # Check first 5 moves for tactics
        tactics = detect_tactics(board, move)
        score += tactics if move[0].isupper() else -tactics
    
    return score

def alpha_beta(game, depth, alpha, beta, maximizing, start_time, max_time=0.95):
    """Alpha-beta search with timing control"""
    if time.time() - start_time > max_time:
        return None, evaluate_position(game.board, game.get_moves())
    
    if depth == 0:
        return None, evaluate_position(game.board, game.get_moves())
    
    moves = list(game.get_moves())
    if not moves:
        if game.status == Game.CHECKMATE:
            return None, -99999 if maximizing else 99999
        return None, 0
    
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
    """Main chess bot function"""
    try:
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
        
        start_time = time.time()
        best_move = moves[0]
        
        # Iterative deepening
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
            
            # Stop if we found mate
            if abs(eval) > 9000:
                break
        
        return best_move
        
    except Exception:
        return moves[0] if moves else None