from Chessnut import Game
import random

PIECE_VALUES = {
    'P': 100,
    'N': 300,
    'B': 300,
    'R': 500,
    'Q': 900,
    'K': 0
}

def evaluate_simple(move, game):
    """Fast evaluation of a move"""
    # Check if move leads to checkmate
    g = Game(game.fen)
    g.apply_move(move)
    if g.status == Game.CHECKMATE:
        return 10000
        
    # Check if move is a capture
    target_square = game.board.get_piece(Game.xy2i(move[2:4]))
    if target_square != ' ':
        piece_value = PIECE_VALUES.get(target_square.upper(), 0)
        return piece_value
        
    # Simple positional bonus for center control
    to_x, to_y = int(move[2]), int(move[3])
    if '3' <= to_y <= '6' and 'c' <= to_x <= 'f':
        return 10
        
    return 0

def chess_bot(obs):
    """Simple and fast chess bot"""
    try:
        # Initialize game
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
            
        # Quick check for immediate mate
        for move in moves[:5]:  # Limit check to first few moves
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        # Evaluate moves and pick best
        scored_moves = [(move, evaluate_simple(move, game)) for move in moves]
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # Return best move or random from top 3 if scores are close
        best_score = scored_moves[0][1]
        good_moves = [move for move, score in scored_moves if score >= best_score - 50]
        return random.choice(good_moves[:3] if len(good_moves) > 2 else good_moves)
        
    except Exception:
        # Fallback to random move if any error occurs
        return moves[0] if moves else None