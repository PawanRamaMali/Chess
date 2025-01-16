from Chessnut import Game
import random

# Piece values for material counting
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

def is_king_in_check(board, king_sq, is_white):
    """Fast check detection for a given king square"""
    # Knight attacks
    knight_moves = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    rank, file = king_sq // 8, king_sq % 8
    enemy_knight = 'n' if is_white else 'N'
    
    for dr, df in knight_moves:
        new_rank, new_file = rank + dr, file + df
        if 0 <= new_rank < 8 and 0 <= new_file < 8:
            if board.get_piece(new_rank * 8 + new_file) == enemy_knight:
                return True
    
    # Diagonal attacks (bishop/queen)
    diagonals = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    enemy_bishop = 'b' if is_white else 'B'
    enemy_queen = 'q' if is_white else 'Q'
    
    for dr, df in diagonals:
        r, f = rank + dr, file + df
        while 0 <= r < 8 and 0 <= f < 8:
            piece = board.get_piece(r * 8 + f)
            if piece in [enemy_bishop, enemy_queen]:
                return True
            if piece != ' ':
                break
            r, f = r + dr, f + df
    
    # Orthogonal attacks (rook/queen)
    lines = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    enemy_rook = 'r' if is_white else 'R'
    
    for dr, df in lines:
        r, f = rank + dr, file + df
        while 0 <= r < 8 and 0 <= f < 8:
            piece = board.get_piece(r * 8 + f)
            if piece in [enemy_rook, enemy_queen]:
                return True
            if piece != ' ':
                break
            r, f = r + dr, f + df
    
    return False

def find_king(board, is_white):
    """Find king's position for given side"""
    king = 'K' if is_white else 'k'
    for i in range(64):
        if board.get_piece(i) == king:
            return i
    return -1

def detect_checkmate_pattern(game, move):
    """Detect common checkmate patterns"""
    g = Game(game.fen)
    g.apply_move(move)
    
    # Find enemy king
    is_white = move[0].isupper()
    king_sq = find_king(g.board, not is_white)
    if king_sq == -1:
        return False
        
    rank, file = king_sq // 8, king_sq % 8
    
    # Check if king is in check
    if not is_king_in_check(g.board, king_sq, not is_white):
        return False
        
    # Check if king has any escape squares
    escape_squares = []
    king_moves = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, df in king_moves:
        new_rank, new_file = rank + dr, file + df
        if 0 <= new_rank < 8 and 0 <= new_file < 8:
            new_sq = new_rank * 8 + new_file
            piece = g.board.get_piece(new_sq)
            if piece == ' ':
                escape_squares.append(new_sq)
    
    # If no escape squares, might be checkmate
    return len(escape_squares) == 0

def evaluate_attack(board, move):
    """Evaluate attacking potential of a move"""
    score = 0
    to_sq = Game.xy2i(move[2:4])
    
    # Control of center
    to_file, to_rank = move[2], int(move[3])
    if to_file in 'de' and 3 <= to_rank <= 5:
        score += 30
    
    # Piece coordination
    piece = board.get_piece(Game.xy2i(move[0:2]))
    piece_type = piece.upper()
    is_white = piece.isupper()
    
    # Support from other pieces
    supports = 0
    for i in range(64):
        supporting_piece = board.get_piece(i)
        if supporting_piece != ' ' and supporting_piece.isupper() == is_white:
            # Check if piece supports the target square
            if piece_type in 'NB':  # Minor pieces supporting each other
                if abs(i - to_sq) in [15, 17]:
                    supports += 1
            elif piece_type in 'RQ':  # Major pieces coordination
                if abs(i - to_sq) in [8, 1]:
                    supports += 2
    
    score += supports * 15
    return score

def search_tactical_sequence(game, depth=3):
    """Search for forcing tactical sequences"""
    if depth == 0:
        return None, 0
    
    moves = list(game.get_moves())
    best_score = -9999
    best_move = None
    
    for move in moves[:8]:  # Look at top 8 moves for performance
        g = Game(game.fen)
        g.apply_move(move)
        
        # Check for immediate mate
        if g.status == Game.CHECKMATE:
            return move, 9999
        
        # Evaluate position
        score = evaluate_attack(game.board, move)
        
        # If in check, look deeper
        if g.status == Game.CHECK:
            _, opponent_score = search_tactical_sequence(g, depth-1)
            score -= opponent_score  # Opponent's best defense
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, best_score

def chess_bot(obs):
    """Advanced tactical chess bot"""
    try:
        game = Game(obs.board)
        moves = list(game.get_moves())
        
        if not moves:
            return None
        
        # 1. Look for immediate checkmate
        for move in moves[:5]:
            g = Game(obs.board)
            g.apply_move(move)
            if g.status == Game.CHECKMATE:
                return move
        
        # 2. Check for common checkmate patterns
        for move in moves:
            if detect_checkmate_pattern(game, move):
                return move
        
        # 3. Search for tactical sequences
        tactical_move, score = search_tactical_sequence(game)
        if tactical_move and score > 500:  # Strong tactical advantage
            return tactical_move
        
        # 4. Evaluate remaining moves
        scored_moves = []
        for move in moves:
            # Basic evaluation
            score = evaluate_attack(game.board, move)
            
            # Material evaluation
            target_piece = game.board.get_piece(Game.xy2i(move[2:4]))
            if target_piece != ' ':
                score += PIECE_VALUES.get(target_piece.upper(), 0)
            
            scored_moves.append((move, score))
        
        # Sort moves by score
        scored_moves.sort(key=lambda x: x[1], reverse=True)
        
        # Select move with minimal randomization
        if len(scored_moves) > 2:
            top_moves = scored_moves[:3]
            weights = [0.7, 0.2, 0.1]  # Higher weight to best move
            return random.choices([m[0] for m in top_moves], weights=weights)[0]
        
        return scored_moves[0][0]
        
    except Exception:
        # Fallback to first legal move
        return moves[0] if moves else None