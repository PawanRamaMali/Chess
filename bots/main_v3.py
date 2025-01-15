from Chessnut import Game
import random

# Piece values with position bonuses pre-calculated
PIECE_VALUES = {
    'P': 100,  # Pawn
    'N': 300,  # Knight
    'B': 310,  # Bishop (slightly higher than Knight)
    'R': 500,  # Rook
    'Q': 900,  # Queen
    'K': 0     # King (not counted in material)
}

def quick_evaluate(board, move):
    """Ultra-fast move evaluation"""
    score = 0
    target_piece = board.get_piece(Game.xy2i(move[2:4]))
    
    # Immediate captures (most important)
    if target_piece != ' ':
        score = PIECE_VALUES.get(target_piece.upper(), 0)
        
        # Capturing with lower value piece is better
        attacker = board.get_piece(Game.xy2i(move[0:2]))
        if attacker != ' ':
            attacker_value = PIECE_VALUES.get(attacker.upper(), 0)
            if attacker_value < score:
                score += 50  # Bonus for favorable trades
                
    # Quick positional scoring
    to_file, to_rank = move[2], move[3]
    
    # Center control
    if to_file in 'de' and to_rank in '45':
        score += 20
        
    # Pawn advancement
    if board.get_piece(Game.xy2i(move[0:2])).upper() == 'P':
        if to_rank in '678':  # Advanced pawns
            score += 30
        if move[3] == '8':  # Promotion
            score += 800
            
    return score

def chess_bot(obs):
    """Optimized chess bot"""
    try:
        # Initialize game state
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
            
        # Early checkmate detection (only first few moves)
        for move in moves[:3]:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        # Quick eval and sort moves
        scored_moves = []
        for move in moves:
            score = quick_evaluate(game.board, move)
            if score > 0:  # Only store promising moves
                scored_moves.append((move, score))
                
        if scored_moves:
            # Sort and take top moves
            scored_moves.sort(key=lambda x: x[1], reverse=True)
            top_score = scored_moves[0][1]
            good_moves = [m for m, s in scored_moves if s >= top_score - 10]
            
            # Select from good moves with slight randomization
            return random.choice(good_moves[:2] if len(good_moves) > 1 else good_moves)
        
        # If no good scoring moves, pick semi-randomly from all moves
        safe_moves = []
        for move in moves:
            # Avoid obvious blunders
            g = Game(obs.board)
            g.apply_move(move)
            if g.status != Game.CHECK:  # Don't move into check
                safe_moves.append(move)
                
        return random.choice(safe_moves if safe_moves else moves)
        
    except Exception:
        # Ultra-safe fallback
        return moves[0] if moves else None