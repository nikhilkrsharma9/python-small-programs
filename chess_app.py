import pygame
import os
import sys

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 600
BOARD_SIZE = 8
SQUARE_SIZE = WIDTH // BOARD_SIZE
FPS = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_SQUARE = (118, 150, 86)
LIGHT_SQUARE = (238, 238, 210)
HIGHLIGHT = (247, 247, 105, 128)  # Highlighted square with some transparency
VALID_MOVE = (186, 202, 68)

# Chess piece representation (empty = 0, and lowercase for black pieces)
# White pieces: P=Pawn, R=Rook, N=Knight, B=Bishop, Q=Queen, K=King
# Black pieces: p=Pawn, r=Rook, n=Knight, b=Bishop, q=Queen, k=King
INITIAL_BOARD = [
    ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
    ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
    ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
]

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Python Chess")
        self.clock = pygame.time.Clock()
        self.load_images()
        self.reset_game()
        
    def load_images(self):
        """Load chess piece images"""
        self.images = {}
        pieces = ['P', 'R', 'N', 'B', 'Q', 'K', 'p', 'r', 'n', 'b', 'q', 'k']
        
        # First try to load from the 'images' subfolder if it exists
        for piece in pieces:
            piece_path = os.path.join('images', f'{piece}.png')
            if os.path.exists(piece_path):
                self.images[piece] = pygame.transform.scale(
                    pygame.image.load(piece_path), (SQUARE_SIZE, SQUARE_SIZE)
                )
        
        # If any images are missing, use colored rectangles with letters as fallback
        for piece in pieces:
            if piece not in self.images:
                # Create a surface with transparent background
                surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                
                # Draw a colored rectangle
                if piece.isupper():  # White pieces
                    pygame.draw.rect(surface, (200, 200, 200, 200), (5, 5, SQUARE_SIZE-10, SQUARE_SIZE-10), border_radius=10)
                else:  # Black pieces
                    pygame.draw.rect(surface, (50, 50, 50, 200), (5, 5, SQUARE_SIZE-10, SQUARE_SIZE-10), border_radius=10)
                
                # Draw the letter on the rectangle
                font = pygame.font.SysFont('Arial', SQUARE_SIZE // 2)
                text = font.render(piece.upper(), True, BLACK if piece.isupper() else WHITE)
                text_rect = text.get_rect(center=(SQUARE_SIZE//2, SQUARE_SIZE//2))
                surface.blit(text, text_rect)
                
                self.images[piece] = surface
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.board = [row[:] for row in INITIAL_BOARD]  # Deep copy
        self.selected_piece = None
        self.turn = 'white'  # White goes first
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        self.check = False
        self.castling_rights = {
            'white': {'kingside': True, 'queenside': True},
            'white_king_moved': False,
            'black': {'kingside': True, 'queenside': True},
            'black_king_moved': False
        }
        self.move_history = []
        
    def is_piece_white(self, piece):
        """Check if a piece is white"""
        return piece.isupper()
    
    def is_valid_position(self, row, col):
        """Check if a position is valid on the board"""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE
    
    def get_piece_at(self, row, col):
        """Get the piece at a specific position"""
        if not self.is_valid_position(row, col):
            return None
        return self.board[row][col]
    
    def calculate_valid_moves(self, row, col):
        """Calculate valid moves for a piece"""
        piece = self.get_piece_at(row, col)
        if piece == ' ':
            return []
        
        is_white = self.is_piece_white(piece)
        moves = []
        
        # Pawn movement
        if piece.upper() == 'P':
            direction = -1 if is_white else 1
            
            # Move forward one square
            if self.is_valid_position(row + direction, col) and self.board[row + direction][col] == ' ':
                moves.append((row + direction, col))
                
                # Move forward two squares from starting position
                if ((is_white and row == 6) or (not is_white and row == 1)) and \
                   self.board[row + 2*direction][col] == ' ':
                    moves.append((row + 2*direction, col))
            
            # Capture diagonally
            for c_offset in [-1, 1]:
                if self.is_valid_position(row + direction, col + c_offset):
                    target = self.board[row + direction][col + c_offset]
                    if target != ' ' and is_white != self.is_piece_white(target):
                        moves.append((row + direction, col + c_offset))
        
        # Rook movement (and part of Queen)
        if piece.upper() in ['R', 'Q']:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                for i in range(1, BOARD_SIZE):
                    r, c = row + i*dr, col + i*dc
                    if not self.is_valid_position(r, c):
                        break
                    target = self.board[r][c]
                    if target == ' ':
                        moves.append((r, c))
                    else:
                        if is_white != self.is_piece_white(target):
                            moves.append((r, c))
                        break
        
        # Bishop movement (and part of Queen)
        if piece.upper() in ['B', 'Q']:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, BOARD_SIZE):
                    r, c = row + i*dr, col + i*dc
                    if not self.is_valid_position(r, c):
                        break
                    target = self.board[r][c]
                    if target == ' ':
                        moves.append((r, c))
                    else:
                        if is_white != self.is_piece_white(target):
                            moves.append((r, c))
                        break
        
        # Knight movement
        if piece.upper() == 'N':
            knight_moves = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for dr, dc in knight_moves:
                r, c = row + dr, col + dc
                if self.is_valid_position(r, c):
                    target = self.board[r][c]
                    if target == ' ' or is_white != self.is_piece_white(target):
                        moves.append((r, c))
        
        # King movement
        if piece.upper() == 'K':
            king_moves = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1), (0, 1),
                (1, -1), (1, 0), (1, 1)
            ]
            for dr, dc in king_moves:
                r, c = row + dr, col + dc
                if self.is_valid_position(r, c):
                    target = self.board[r][c]
                    if target == ' ' or is_white != self.is_piece_white(target):
                        moves.append((r, c))
            
            # Castling
            if is_white and not self.castling_rights['white_king_moved']:
                # Kingside castling
                if self.castling_rights['white']['kingside'] and \
                   all(self.board[7][c] == ' ' for c in range(5, 7)) and \
                   self.board[7][7] == 'R':
                    moves.append((7, 6))  # King's final position after castling
                
                # Queenside castling
                if self.castling_rights['white']['queenside'] and \
                   all(self.board[7][c] == ' ' for c in range(1, 4)) and \
                   self.board[7][0] == 'R':
                    moves.append((7, 2))  # King's final position after castling
            
            elif not is_white and not self.castling_rights['black_king_moved']:
                # Kingside castling
                if self.castling_rights['black']['kingside'] and \
                   all(self.board[0][c] == ' ' for c in range(5, 7)) and \
                   self.board[0][7] == 'r':
                    moves.append((0, 6))  # King's final position after castling
                
                # Queenside castling
                if self.castling_rights['black']['queenside'] and \
                   all(self.board[0][c] == ' ' for c in range(1, 4)) and \
                   self.board[0][0] == 'r':
                    moves.append((0, 2))  # King's final position after castling
        
        return moves
    
    def move_piece(self, from_row, from_col, to_row, to_col):
        """Move a piece on the board"""
        piece = self.board[from_row][from_col]
        captured_piece = self.board[to_row][to_col]
        
        # Store move in history
        self.move_history.append({
            'piece': piece,
            'from': (from_row, from_col),
            'to': (to_row, to_col),
            'captured': captured_piece
        })
        
        # Handle castling
        if piece.upper() == 'K' and abs(from_col - to_col) == 2:
            # This is a castling move
            is_white = self.is_piece_white(piece)
            rook_row = 7 if is_white else 0
            
            # Kingside castling
            if to_col == 6:
                # Move the rook as well
                self.board[rook_row][5] = self.board[rook_row][7]  # Move rook
                self.board[rook_row][7] = ' '  # Remove rook from original position
            
            # Queenside castling
            elif to_col == 2:
                # Move the rook as well
                self.board[rook_row][3] = self.board[rook_row][0]  # Move rook
                self.board[rook_row][0] = ' '  # Remove rook from original position
        
        # Update castling rights
        if piece.upper() == 'K':
            if self.is_piece_white(piece):
                self.castling_rights['white_king_moved'] = True
            else:
                self.castling_rights['black_king_moved'] = True
        
        # Update rook movement for castling rights
        if piece.upper() == 'R':
            is_white = self.is_piece_white(piece)
            if is_white:
                if from_row == 7 and from_col == 0:  # Queenside rook
                    self.castling_rights['white']['queenside'] = False
                elif from_row == 7 and from_col == 7:  # Kingside rook
                    self.castling_rights['white']['kingside'] = False
            else:
                if from_row == 0 and from_col == 0:  # Queenside rook
                    self.castling_rights['black']['queenside'] = False
                elif from_row == 0 and from_col == 7:  # Kingside rook
                    self.castling_rights['black']['kingside'] = False
        
        # Check for pawn promotion (simplified - always promotes to queen)
        if piece.upper() == 'P' and (to_row == 0 or to_row == 7):
            piece = 'Q' if self.is_piece_white(piece) else 'q'
        
        # Update the board
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = ' '
        
        # Switch turns
        self.turn = 'black' if self.turn == 'white' else 'white'
        
        # Check for checkmate (simplified)
        self.check_for_checkmate()
    
    def check_for_checkmate(self):
        """Check if the game is over (simplified)"""
        # This is a simplified version - a real chess app would need more logic
        # For now, we'll just check if a king is missing
        white_king_exists = any('K' in row for row in self.board)
        black_king_exists = any('k' in row for row in self.board)
        
        if not white_king_exists:
            self.game_over = True
            self.winner = 'black'
        elif not black_king_exists:
            self.game_over = True
            self.winner = 'white'
    
    def handle_click(self, row, col):
        """Handle mouse click on the board"""
        if self.game_over:
            return
        
        piece = self.get_piece_at(row, col)
        
        # If a piece is already selected
        if self.selected_piece:
            sel_row, sel_col = self.selected_piece
            
            # Check if the clicked position is a valid move
            if (row, col) in self.valid_moves:
                self.move_piece(sel_row, sel_col, row, col)
                self.selected_piece = None
                self.valid_moves = []
            else:
                # If clicking on own piece, select it instead
                if piece != ' ' and ((self.turn == 'white' and self.is_piece_white(piece)) or 
                                   (self.turn == 'black' and not self.is_piece_white(piece))):
                    self.selected_piece = (row, col)
                    self.valid_moves = self.calculate_valid_moves(row, col)
                else:
                    # Clicking elsewhere deselects
                    self.selected_piece = None
                    self.valid_moves = []
        
        # If no piece is selected yet
        else:
            if piece != ' ' and ((self.turn == 'white' and self.is_piece_white(piece)) or 
                               (self.turn == 'black' and not self.is_piece_white(piece))):
                self.selected_piece = (row, col)
                self.valid_moves = self.calculate_valid_moves(row, col)
    
    def draw_board(self):
        """Draw the chess board"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # Draw the square
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
                # Highlight selected piece
                if self.selected_piece and self.selected_piece == (row, col):
                    pygame.draw.rect(self.screen, HIGHLIGHT, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                
                # Highlight valid moves
                if (row, col) in self.valid_moves:
                    pygame.draw.circle(self.screen, VALID_MOVE, 
                                      (col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                                       row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                      SQUARE_SIZE // 6)
                
                # Draw the piece
                piece = self.board[row][col]
                if piece != ' ':
                    piece_img = self.images[piece]
                    self.screen.blit(piece_img, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    def draw_game_over(self):
        """Draw game over message"""
        if self.game_over:
            # Create a semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            # Draw game over text
            font = pygame.font.SysFont('Arial', 48)
            game_over_text = font.render('Game Over', True, WHITE)
            winner_text = font.render(f'{self.winner.capitalize()} wins!', True, WHITE)
            
            self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
            self.screen.blit(winner_text, (WIDTH // 2 - winner_text.get_width() // 2, HEIGHT // 2))
            
            # Draw restart button
            restart_font = pygame.font.SysFont('Arial', 32)
            restart_text = restart_font.render('Click to Restart', True, WHITE)
            self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 60))

    def run(self):
        """Main game loop"""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                    # Get board coordinates from mouse position
                    mouse_pos = pygame.mouse.get_pos()
                    col = mouse_pos[0] // SQUARE_SIZE
                    row = mouse_pos[1] // SQUARE_SIZE
                    
                    if self.game_over:
                        # Click anywhere to restart when game is over
                        self.reset_game()
                    else:
                        self.handle_click(row, col)
            
            # Draw everything
            self.draw_board()
            if self.game_over:
                self.draw_game_over()
            
            # Update the display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()