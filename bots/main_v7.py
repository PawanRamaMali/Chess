from Chessnut import Game
import random

# Enhanced piece values considering mobility and position
PIECE_VALUES = {
    'P': 100,   # Pawn
    'N': 325,   # Knight (slightly higher for mobility)
    'B': 335,   # Bishop (pair bonus handled separately)
    'R': 500,   # Rook
    'Q': 900,   # Queen
    'K': 20000  # King
}

# Strategic squares for different pieces
STRATEGIC_SQUARES = {
    'P': {  # Pawn control squares
        'd4': 35, 'e4': 35, 'd5': 35, 'e5': 35,  # Center
        'c5': 25, 'f5': 25, 'c4': 25, 'f4': 25,  # Extended center
    },
    'N': {  # Knight outposts
        'd5': 30, 'e5': 30, 'c5': 25, 'f5': 25,
        'd4': 25, 'e4': 25, 'c4': 20, 'f4': 20
    },
    'B': {  # Bishop control diagonals
        'c4': 20, 'f4': 20, 'b3': 15, 'g3': 15,
        'c5': 20, 'f5': 20, 'b6': 15, 'g6': 15
    }
}

def get_position_signature(board):
    """Get unique position characteristics"""
    pawns_white = pawns_black = bishops_white = bishops_black = 0
    
    for i in range(64):
        piece = board.get_piece(i)
        if piece == 'P':
            pawns_white |= (1 << i)
        elif piece == 'p':
            pawns_black |= (1 << i)
        elif piece == 'B':
            bishops_white += 1
        elif piece == 'b':
            bishops_black += 1
            
    return {
        'pawns_white': pawns_white,
        'pawns_black': pawns_black,
        'bishop_pair_white': bishops_white >= 2,
        'bishop_pair_black': bishops_black >= 2
    }

def evaluate_pawn_structure(sig, side_to_move):
    """Advanced pawn structure evaluation"""
    score = 0
    
    pawns = sig['pawns_white'] if side_to_move else sig['pawns_black']
    opp_pawns = sig['pawns_black'] if side_to_move else sig['pawns_white']
    
    # Doubled pawns penalty
    for file in range(8):
        file_pawns = bin(pawns & (0x0101010101010101 << file)).count('1')
        if file_pawns > 1:
            score -= 20 * (file_pawns - 1)
    
    # Isolated pawns penalty
    for file in range(8):
        if file > 0:
            left_file = pawns & (0x0101010101010101 << (file - 1))
        else:
            left_file = 0
        if file < 7:
            right_file = pawns & (0x0101010101010101 << (file + 1))
        else:
            right_file = 0
        
        if (pawns & (0x0101010101010101 << file)) and not (left_file or right_file):
            score -= 15
    
    return score

def evaluate_mobility_and_control(board, move, is_endgame):
    """Evaluate piece mobility and position control"""
    score = 0
    from_sq = Game.xy2i(move[0:2])
    to_sq = Game.xy2i(move[2:4])
    piece = board.get_piece(from_sq)
    piece_type = piece.upper()
    
    # Strategic square control
    move_str = f"{move[2]}{move[3]}"
    if piece_type in STRATEGIC_SQUARES and move_str in STRATEGIC_SQUARES[piece_type]:
        score += STRATEGIC_SQUARES[piece_type][move_str]
        
        # Additional bonus for protected pieces
        if is_protected(board, to_sq, piece.isupper()):
            score += 10
    
    # Piece-specific mobility
    if piece_type == 'N':
        score += evaluate_knight_mobility(board, to_sq)
    elif piece_type == 'B':
        score += evaluate_bishop_mobility(board, to_sq)
    elif piece_type == 'R':
        score += evaluate_rook_mobility(board, to_sq, is_endgame)
    elif piece_type == 'Q':
        score += evaluate_queen_mobility(board, to_sq, is_endgame)
    
    return score

def evaluate_king_safety(board, king_sq, is_endgame):
    """Evaluate king safety and pawn shield"""
    score = 0
    
    if not is_endgame:
        # Check pawn shield
        rank = king_sq // 8
        file = king_sq % 8
        
        for f in range(max(0, file-1), min(8, file+2)):
            for r in range(rank-1, rank+1):
                if 0 <= r < 8:
                    idx = r * 8 + f
                    if board.get_piece(idx).upper() == 'P':
                        score += 15
        
        # Open files near king penalty
        for f in range(max(0, file-1), min(8, file+2)):
            has_pawn = False
            for r in range(8):
                if board.get_piece(r * 8 + f).upper() == 'P':
                    has_pawn = True
                    break
            if not has_pawn:
                score -= 20
    
    return score

def is_protected(board, sq, is_white):
    """Check if square is protected by pawns"""
    rank = sq // 8
    file = sq % 8
    
    # Check protecting pawns
    pawn = 'P' if is_white else 'p'
    if is_white:
        if rank > 0:
            if file > 0 and board.get_piece((rank-1)*8 + file-1) == pawn:
                return True
            if file < 7 and board.get_piece((rank-1)*8 + file+1) == pawn:
                return True
    else:
        if rank < 7:
            if file > 0 and board.get_piece((rank+1)*8 + file-1) == pawn:
                return True
            if file < 7 and board.get_piece((rank+1)*8 + file+1) == pawn:
                return True
    
    return False

def evaluate_position(board, move, is_endgame):
    """Master evaluation function"""
    score = 0
    
    # Get position characteristics
    sig = get_position_signature(board)
    
    # Material and basic positional evaluation
    from_sq = Game.xy2i(move[0:2])
    to_sq = Game.xy2i(move[2:4])
    moving_piece = board.get_piece(from_sq)
    target_piece = board.get_piece(to_sq)
    
    # Capture evaluation
    if target_piece != ' ':
        score += PIECE_VALUES[target_piece.upper()]
        # Exchange evaluation
        if moving_piece != ' ':
            attacker_value = PIECE_VALUES[moving_piece.upper()]
            if attacker_value < PIECE_VALUES[target_piece.upper()]:
                score += 50  # Winning material
    
    # Mobility and control
    score += evaluate_mobility_and_control(board, move, is_endgame)
    
    # Pawn structure
    score += evaluate_pawn_structure(sig, moving_piece.isupper())
    
    # King safety
    king_sq = -1
    for i in range(64):
        if board.get_piece(i).upper() == 'K':
            king_sq = i
            break
    if king_sq != -1:
        score += evaluate_king_safety(board, king_sq, is_endgame)
    
    # Bishop pair bonus
    if sig['bishop_pair_white' if moving_piece.isupper() else 'bishop_pair_black']:
        score += 30
    
    # Piece-specific bonuses
    if moving_piece.upper() == 'P':
        # Passed pawn bonus
        rank = int(move[3])
        if moving_piece.isupper():
            score += 20 * rank
        else:
            score += 20 * (9 - rank)
    
    return score

def chess_bot(obs):
    """Advanced chess engine"""
    try:
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
            
        # Quick tactical check
        for move in moves[:3]:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        # Determine game phase
        total_pieces = sum(1 for i in range(64) if game.board.get_piece(i) != ' ')
        is_endgame = total_pieces <= 16
        
        # Evaluate moves
        scored_moves = []
        for move in moves:
            score = evaluate_position(game.board, move, is_endgame)
            scored_moves.append((move, score))
        
        # Sort moves by score
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # Select move with controlled randomization
        if len(scored_moves) > 2:
            weights = [0.7, 0.2, 0.1]  # Probability distribution
            selected_moves = scored_moves[:3]
            move = random.choices([m[0] for m in selected_moves], weights=weights)[0]
        else:
            move = scored_moves[0][0]
        
        return move
        
    except Exception:
        return moves[0] if moves else None