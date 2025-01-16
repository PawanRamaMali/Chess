from Chessnut import Game
import random

# Optimized piece values for faster calculation
PIECE_VALUES = {
    'P': 100,    # Pawn
    'N': 320,    # Knight
    'B': 330,    # Bishop
    'R': 500,    # Rook
    'Q': 900,    # Queen
    'K': 20000   # King - high value to protect it
}

# Critical squares for development and control
CENTER_SQUARES = {
    'e4': 30, 'd4': 30, 'e5': 25, 'd5': 25,
    'c3': 15, 'f3': 15, 'c6': 15, 'f6': 15
}

def evaluate_development(board, is_endgame):
    """Evaluate piece development and structure"""
    score = 0
    pieces_developed = 0
    
    # Check piece development from starting squares
    if not is_endgame:
        for i in range(64):
            piece = board.get_piece(i)
            if piece != ' ':
                x, y = i % 8, i // 8
                
                if piece.upper() == 'P':
                    # Central pawns
                    if 2 <= x <= 5 and 3 <= y <= 4:
                        score += 20
                    # Passed pawns
                    if y in (1, 6):
                        score += 50
                elif piece.upper() in 'NB':
                    # Developed minor pieces
                    if (y not in (0, 7)) or (x in (2, 5)):
                        pieces_developed += 1
                        score += 15
                elif piece.upper() == 'K':
                    # King safety in opening/middlegame
                    if not is_endgame:
                        if y == 0 and 5 <= x <= 7:  # Kingside castle
                            score += 60
                        elif y == 7 and 5 <= x <= 7:
                            score -= 60
    
    return score + (pieces_developed * 10)

def evaluate_position(board, move, last_move):
    """Strategic position evaluation"""
    score = 0
    from_sq = Game.xy2i(move[0:2])
    to_sq = Game.xy2i(move[2:4])
    moving_piece = board.get_piece(from_sq)
    target_piece = board.get_piece(to_sq)
    
    # Material evaluation
    if target_piece != ' ':
        capture_value = PIECE_VALUES.get(target_piece.upper(), 0)
        attacker_value = PIECE_VALUES.get(moving_piece.upper(), 0)
        score += capture_value
        
        # Favorable exchanges bonus
        if attacker_value < capture_value:
            score += (capture_value - attacker_value) // 2
    
    # Development and control
    piece_type = moving_piece.upper()
    move_str = f"{move[2]}{move[3]}"
    
    if move_str in CENTER_SQUARES:
        score += CENTER_SQUARES[move_str]
    
    # Pawn structure
    if piece_type == 'P':
        # Central pawns
        if move[2] in 'de' and move[3] in '45':
            score += 25
        # Pawn advancement
        rank = int(move[3])
        if rank >= 5:
            score += 15 * (rank - 4)
        # Promotion
        if rank == 8:
            score += 800
    
    # Mobility and control
    if piece_type in 'NB':
        if int(move[3]) in (3, 4, 5):  # Controlling central ranks
            score += 15
            
    # King safety
    if piece_type == 'K':
        # Penalize early king movement
        if not any(p.upper() == 'Q' for p in str(board)):
            score -= 50
            
    # Piece coordination
    if last_move:
        last_to = Game.xy2i(last_move[2:4])
        if abs(to_sq - last_to) <= 8:  # Pieces supporting each other
            score += 10
            
    return score

def chess_bot(obs):
    """Enhanced strategic chess bot"""
    try:
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
            
        # Check for immediate tactical opportunities
        for move in moves[:5]:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
                
        # Determine game phase
        total_pieces = sum(1 for i in range(64) if game.board.get_piece(i) != ' ')
        is_endgame = total_pieces <= 16
        
        # Get last move for piece coordination
        last_move = obs.get('lastMove', '')
        
        # Strategic evaluation of all moves
        scored_moves = []
        for move in moves:
            # Base position score
            score = evaluate_position(game.board, move, last_move)
            
            # Add development score if not endgame
            if not is_endgame:
                g = Game(obs.board)
                g.apply_move(move)
                score += evaluate_development(g.board, is_endgame)
            
            scored_moves.append((move, score))
            
        # Sort moves by score
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # Select move with some randomization to avoid predictability
        if len(scored_moves) > 2:
            top_moves = scored_moves[:3]
            weights = [0.6, 0.3, 0.1]  # Probability distribution for top 3 moves
            move = random.choices([m[0] for m in top_moves], weights=weights)[0]
        else:
            move = scored_moves[0][0]
            
        return move
        
    except Exception:
        return moves[0] if moves else None