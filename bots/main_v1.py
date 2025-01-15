from Chessnut import Game
import random

def chess_bot(obs):
    """
    Simple chess bot that prioritizes checkmates, captures, queen promotions, then random moves.
    Args:
        obs: An object with a 'board' attribute representing the current board state as a FEN string.
    Returns:
        A string representing the chosen move in UCI notation (e.g., "e2e4")
    """
    game = Game(obs.board)
    moves = list(game.get_moves())
    
    if not moves:
        return None
        
    # Store board for reuse
    board = game.board
    
    # 1. Find checkmate moves (check only first 8 moves for performance)
    for move in moves[:8]:
        g = Game(obs.board)
        g.apply_move(move)
        if g.status == Game.CHECKMATE:
            return move
            
    # 2. Find capture moves using pre-computed board
    capture_moves = [
        move for move in moves 
        if board.get_piece(Game.xy2i(move[2:4])) != ' '
    ]
    if capture_moves:
        return capture_moves[0]
        
    # 3. Find queen promotion moves
    promo_moves = [move for move in moves if move.endswith('q')]
    if promo_moves:
        return promo_moves[0]
        
    # 4. Random move if no better options found
    return random.choice(moves)