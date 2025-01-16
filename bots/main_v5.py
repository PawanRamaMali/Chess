from Chessnut import Game
import random

# Compressed piece-square tables using relative values
PST = {
    'P': [   # Pawn position values (focused on center control and advancement)
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 27, 27, 10,  5,  5,
        0,  0,  0, 25, 25,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [   # Knight position values (encourages development and center control)
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

# Dynamic piece values that change based on game phase
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0
}

def get_game_phase(board):
    """
    Determine game phase based on piece count
    Returns: float between 0 (opening) and 1 (endgame)
    """
    pieces = 0
    for i in range(64):
        piece = board.get_piece(i)
        if piece != ' ' and piece.upper() != 'K' and piece.upper() != 'P':
            pieces += 1
    return 1.0 - (min(pieces, 12) / 12.0)

def evaluate_move(board, move, phase):
    """
    Smart move evaluation considering multiple factors
    """
    score = 0
    from_sq = Game.xy2i(move[0:2])
    to_sq = Game.xy2i(move[2:4])
    moving_piece = board.get_piece(from_sq)
    target_piece = board.get_piece(to_sq)
    
    # Material gain/loss evaluation
    if target_piece != ' ':
        score += PIECE_VALUES.get(target_piece.upper(), 0)
        # Encourage trades when ahead, discourage when behind
        if moving_piece != ' ':
            attacker_value = PIECE_VALUES.get(moving_piece.upper(), 0)
            if attacker_value < PIECE_VALUES.get(target_piece.upper(), 0):
                score += 50  # Good trade
    
    # Positional evaluation
    piece_type = moving_piece.upper()
    if piece_type in PST:
        # Get positional score based on game phase
        if piece_type == 'P':
            score += PST['P'][to_sq] * (1 - phase)  # Pawns more important in opening/middlegame
        elif piece_type == 'N':
            score += PST['N'][to_sq] * (1 - phase)  # Knights better in closed positions
    
    # Advanced pawn handling
    if piece_type == 'P':
        to_rank = int(move[3])
        if to_rank in [6, 7, 8]:  # Advanced pawns
            score += 10 * to_rank  # Progressive bonus for advancement
        if move[3] == '8':  # Promotion
            score += 800
    
    # King safety (early/middle game)
    if piece_type == 'K' and phase < 0.7:
        if not (move[2] in 'gh' and move[3] in '12'):  # Penalize king movement from safe corner
            score -= 50
    
    # Control of critical squares
    if move[2] in 'de' and move[3] in '456':  # Center control
        score += 20 * (1 - phase)  # Center more important in opening/middlegame
    
    return score

def chess_bot(obs):
    """
    Enhanced chess bot with smart evaluation and adaptive play
    """
    try:
        # Initialize game state
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
        
        # Quick check for immediate mate
        for move in moves[:3]:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        # Determine game phase
        phase = get_game_phase(game.board)
        
        # Evaluate all legal moves
        scored_moves = []
        for move in moves:
            score = evaluate_move(game.board, move, phase)
            scored_moves.append((move, score))
        
        # Sort moves by score
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # Select move based on game phase and position
        if phase < 0.3:  # Opening/early middlegame
            # More randomization early, choose from top moves
            good_moves = [m for m, s in scored_moves[:3]]
            return random.choice(good_moves)
        elif phase < 0.7:  # Late middlegame
            # Less randomization, prefer best moves
            good_moves = [m for m, s in scored_moves[:2]]
            return random.choice(good_moves)
        else:  # Endgame
            # Minimal randomization, usually best move
            return scored_moves[0][0]
            
    except Exception:
        # Safe fallback
        return moves[0] if moves else None