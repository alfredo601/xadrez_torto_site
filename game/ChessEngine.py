# ChessEngine.py
# VERSÃO 4.7 - Garante a atualização visual da captura do Rei

class GameState:
    def __init__(self):
        self.board = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp', 'bp'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['--', '--', '--', '--', '--', '--', '--', '--'],
            ['wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp', 'wp'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        self.white_to_move = True
        self.move_log = []
        self.game_over = False
        self.winner = None
        
        self.en_passant_possible = ()
        self.castling_rights = {'wks': True, 'wqs': True, 'bks': True, 'bqs': True}
        self.castling_log = [self.castling_rights.copy()]

        self.king_pos = {'w': (7, 4), 'b': (0, 4)}
        self.vision_board = [['??' for _ in range(8)] for _ in range(8)]
        self.calculate_vision()  # Usa comportamento padrão na inicialização

    def make_move(self, start_pos, end_pos, promotion_piece='Q'):
        # Retorna True se o movimento for bem-sucedido, False caso contrário.
        if self.game_over: return False

        start_row, start_col = start_pos
        end_row, end_col = end_pos
        
        # Validação básica
        if start_row is None or start_col is None or end_row is None or end_col is None: return False
        
        piece_moved = self.board[start_row][start_col]
        
        if (piece_moved == '--') or \
           (piece_moved[0] == 'w' and not self.white_to_move) or \
           (piece_moved[0] == 'b' and self.white_to_move):
            return False

        valid_moves = self.get_valid_moves(start_row, start_col)
        if end_pos not in valid_moves:
            return False

        piece_captured = self.board[end_row][end_col]
        self.board[start_row][start_col] = '--'

        # En passant
        if piece_moved[1] == 'p' and end_pos == self.en_passant_possible:
            self.board[start_row][end_col] = '--'
        
        # Castling
        if piece_moved[1] == 'K' and abs(start_col - end_col) == 2:
            if end_col - start_col == 2:
                self.board[end_row][end_col-1] = self.board[end_row][end_col+1]
                self.board[end_row][end_col+1] = '--'
            else:
                self.board[end_row][end_col+1] = self.board[end_row][end_col-2]
                self.board[end_row][end_col-2] = '--'
        
        # Coroação de peão
        if piece_moved[1] == 'p' and ((piece_moved[0] == 'w' and end_row == 0) or (piece_moved[0] == 'b' and end_row == 7)):
            self.board[end_row][end_col] = piece_moved[0] + promotion_piece
            self.move_log.append(f"{piece_moved} de {start_pos} para {end_pos} promovido para {piece_moved[0] + promotion_piece}")
        else:
            self.board[end_row][end_col] = piece_moved
            self.move_log.append(f"{piece_moved} de {start_pos} para {end_pos}")

        if piece_moved[1] == 'p' and abs(start_row - end_row) == 2:
            self.en_passant_possible = ((start_row + end_row) // 2, start_col)
        else:
            self.en_passant_possible = ()

        if piece_moved[1] == 'K':
            self.king_pos[piece_moved[0]] = end_pos

        self.update_castle_rights(start_row, start_col, piece_moved)
        self.castling_log.append(self.castling_rights.copy())

        if piece_captured != '--' and piece_captured[1] == 'K':
            self.game_over = True
            self.winner = "Brancas" if self.white_to_move else "Pretas"
        
        if not self.game_over:
            self.white_to_move = not self.white_to_move
        
        return True # Movimento foi bem-sucedido
    
    def is_pawn_promotion(self, start_pos, end_pos):
        """Verifica se o movimento resulta em coroação de peão"""
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        
        if piece[1] == 'p':
            if (piece[0] == 'w' and end_row == 0) or (piece[0] == 'b' and end_row == 7):
                return True
        return False

    def get_valid_moves(self, r, c):
        moves = []
        piece = self.board[r][c]
        piece_color = piece[0]

        if piece[1] == 'p':
            direction = -1 if piece_color == 'w' else 1
            if self.is_in_bounds(r + direction, c) and self.board[r + direction][c] == '--':
                moves.append((r + direction, c))
                if (r == 6 and piece_color == 'w') or (r == 1 and piece_color == 'b'):
                    if self.is_in_bounds(r + 2 * direction, c) and self.board[r + 2 * direction][c] == '--':
                        moves.append((r + 2 * direction, c))
            for dc in [-1, 1]:
                if self.is_in_bounds(r + direction, c + dc):
                    if self.board[r + direction][c + dc][0] != piece_color and self.board[r + direction][c + dc] != '--':
                        moves.append((r + direction, c + dc))
                    elif (r + direction, c + dc) == self.en_passant_possible:
                        moves.append((r + direction, c + dc))

        elif piece[1] == 'K':
            king_moves = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in king_moves:
                end_row, end_col = r + dr, c + dc
                if self.is_in_bounds(end_row, end_col) and (self.board[end_row][end_col] == '--' or self.board[end_row][end_col][0] != piece_color):
                    moves.append((end_row, end_col))
            self.get_castle_moves(r, c, moves)
        
        elif piece[1] == 'N':
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in knight_moves:
                end_row, end_col = r + dr, c + dc
                if self.is_in_bounds(end_row, end_col) and (self.board[end_row][end_col] == '--' or self.board[end_row][end_col][0] != piece_color):
                    moves.append((end_row, end_col))
        else:
            directions = []
            if piece[1] == 'R': directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            elif piece[1] == 'B': directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif piece[1] == 'Q': directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    end_row, end_col = r + dr * i, c + dc * i
                    if self.is_in_bounds(end_row, end_col):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == '--': moves.append((end_row, end_col))
                        elif end_piece[0] != piece_color:
                            moves.append((end_row, end_col))
                            break
                        else: break
                    else: break
        return moves

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '--':
                    turn = piece[0]
                    if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                        valid_moves = self.get_valid_moves(r, c)
                        for move in valid_moves:
                            moves.append(((r, c), move))
        return moves
        
    def get_castle_moves(self, r, c, moves):
        color = 'w' if self.white_to_move else 'b'
        if self.castling_rights[color + 'ks']:
            if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
                moves.append((r, c+2))
        
        if self.castling_rights[color + 'qs']:
            if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
                moves.append((r, c-2))

    def update_castle_rights(self, r, c, piece):
        color = piece[0]
        if piece[1] == 'K':
            self.castling_rights[color + 'ks'] = False
            self.castling_rights[color + 'qs'] = False
        elif piece[1] == 'R':
            if r == 7:
                if c == 0: self.castling_rights['wqs'] = False
                elif c == 7: self.castling_rights['wks'] = False
            elif r == 0:
                if c == 0: self.castling_rights['bqs'] = False
                elif c == 7: self.castling_rights['bks'] = False
    
    def calculate_vision(self, viewing_player_color=None):
        # --- CORREÇÃO ADICIONADA AQUI ---
        # Se o jogo acabou, simplesmente revela o tabuleiro inteiro.
        if self.game_over:
            # Cria uma cópia do tabuleiro real para o tabuleiro de visão
            self.vision_board = [row[:] for row in self.board]
            return # Para a execução aqui, ignorando a lógica de visão normal

        # Se o jogo não acabou, executa a lógica normal de visão
        self.vision_board = [['??' for _ in range(8)] for _ in range(8)]
        # Use a cor do jogador que está vendo, não necessariamente quem está jogando
        player_color = viewing_player_color if viewing_player_color else ('w' if self.white_to_move else 'b')
        
        for r in range(8):
            for c in range(8):
                if self.board[r][c][0] == player_color:
                    self.vision_board[r][c] = self.board[r][c]

        for r in range(8):
            for c in range(8):
                if self.board[r][c][0] == player_color:
                    self.get_piece_vision(r, c, self.board[r][c])

    def get_piece_vision(self, r, c, piece):
        piece_type = piece[1]
        player_color = piece[0]
        
        if piece_type == 'p':
            direction = -1 if player_color == 'w' else 1
            if self.is_in_bounds(r + direction, c) and self.vision_board[r + direction][c] == '??':
                if self.board[r + direction][c] == '--': self.vision_board[r + direction][c] = '--'
                else: self.vision_board[r + direction][c] = 'XX'
            
            if ((r == 6 and player_color == 'w') or (r == 1 and player_color == 'b')) and self.is_in_bounds(r + 2 * direction, c) and self.board[r + direction][c] == '--' and self.board[r + 2 * direction][c] == '--':
                if self.vision_board[r + 2 * direction][c] == '??': self.vision_board[r + 2 * direction][c] = '--'

            for dc in [-1, 1]:
                if self.is_in_bounds(r + direction, c + dc):
                    target_piece = self.board[r + direction][c + dc]
                    is_enemy = (target_piece != '--' and target_piece[0] != player_color)
                    if is_enemy:
                        self.vision_board[r + direction][c + dc] = target_piece
                    elif (r + direction, c + dc) == self.en_passant_possible:
                        self.vision_board[r + direction][c + dc] = '--'

        elif piece_type in ['R', 'B', 'Q', 'N', 'K']:
            directions = []
            distance = 8
            if piece_type == 'R': directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            elif piece_type == 'B': directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif piece_type == 'Q': directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif piece_type == 'N':
                directions = [(-2, 1), (-2, -1), (-1, 2), (-1, -2), (1, 2), (1, -2), (2, 1), (2, -1)]
                distance = 1
            elif piece_type == 'K':
                directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                distance = 1
            
            for dr, dc in directions:
                for i in range(1, distance + 1):
                    end_row, end_col = r + dr * i, c + dc * i
                    if self.is_in_bounds(end_row, end_col):
                        if self.vision_board[end_row][end_col] == '??' or self.vision_board[end_row][end_col] == 'XX':
                            self.vision_board[end_row][end_col] = self.board[end_row][end_col]
                        if self.board[end_row][end_col] != '--':
                            break
                    else:
                        break

    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8