# ChessAI.py
# Módulo de Inteligência Artificial para o Xadrez Torto

import random

# Dicionário com a pontuação de cada peça. Usado pela IA para tomar decisões.
# O Rei tem valor 0 pois o objetivo não é ter um rei valioso, mas seguro.
piece_scores = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'p': 1}

def find_best_move(gs):
    """
    A função principal da IA.
    Recebe o estado do jogo (gs) e retorna o melhor movimento que a IA pode fazer.
    Estratégia: Gulosa (Greedy). Prioriza a captura de maior valor.
    """
    # Pega todos os movimentos possíveis para o jogador atual (a IA)
    possible_moves = gs.get_all_possible_moves()

    # Se não houver movimentos, não há o que fazer
    if not possible_moves:
        return None

    best_move = None
    best_value = -1

    # Analisa cada movimento para ver se é uma captura valiosa
    for move in possible_moves:
        start_pos, end_pos = move
        end_row, end_col = end_pos
        captured_piece = gs.board[end_row][end_col]

        # Verifica se o movimento resulta em uma captura
        if captured_piece != '--':
            capture_value = piece_scores[captured_piece[1]] # Pega o valor da peça (ex: 'p' de 'bp')
            
            # Se esta captura for a melhor que vimos até agora, armazena o movimento
            if capture_value > best_value:
                best_value = capture_value
                best_move = move

    # Se, após analisar todos os movimentos, encontramos uma boa captura, a executamos
    if best_move is not None:
        return best_move
    else:
        # Se não houver nenhuma captura possível, faz um movimento aleatório
        return random.choice(possible_moves)