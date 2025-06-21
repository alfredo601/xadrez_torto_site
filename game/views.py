from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.templatetags.static import static
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db import models
from .models import Game, Challenge
from . import ChessEngine
from . import ChessAI
from . import rating_logic  # Importa nossa nova lógica de rating
import json
from datetime import datetime

# ===================================================================
# View da Página Inicial
# ===================================================================
def home_view(request):
    online_users = []
    # Pega todos os usuários do banco de dados, exceto o superusuário se houver
    all_users = User.objects.filter(is_superuser=False)

    for user in all_users:
        # Para cada usuário, verifica se a chave 'seen_{username}' existe no cache
        if cache.get(f'seen_{user.username}'):
            # Não queremos nos listar como online para nós mesmos
            if user != request.user:
                online_users.append(user)
    
    context = {
        'online_users': online_users
    }
    return render(request, 'game/home.html', context)

# ===================================================================
# Views de Autenticação
# ===================================================================
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'game/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'game/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# ===================================================================
# Views de Lógica do Jogo
# ===================================================================
@login_required
def create_game_view(request):
    game_engine = ChessEngine.GameState()
    board_state_json = json.dumps(game_engine.__dict__)
    new_game = Game.objects.create(
        white_player=request.user,
        board_state=board_state_json,
        turn='w'
    )
    return redirect('game_view', game_id=new_game.id)

@login_required
def game_view(request, game_id):
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        return redirect('home')

    # Verifica se o usuário é um dos jogadores
    if game.game_type == 'pvp' and request.user not in [game.white_player, game.black_player]:
        return redirect('home')
    elif game.game_type == 'ai' and request.user != game.white_player:
        return redirect('home')

    game_state_dict = json.loads(game.board_state)
    gs = ChessEngine.GameState()
    gs.__dict__.update(game_state_dict)
    
    # Determina a cor do jogador atual
    if game.game_type == 'pvp':
        player_color = game.get_player_color(request.user)
    else:
        # Para jogos contra IA, o jogador sempre é branco
        player_color = 'w'
    
    # Não inverte o tabuleiro aqui - a orientação será tratada no frontend
    
    image_paths = {
        piece: static(f'images/{piece}.png')
        for piece in ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    }
    
    # Recalcula a visão para o jogador específico
    gs.calculate_vision(player_color)
    
    # Verificar se é o turno do jogador atual
    is_my_turn = False
    is_pvp = game.game_type == 'pvp'
    if is_pvp:
        is_my_turn = game.is_player_turn(request.user)
    else:
        is_my_turn = gs.white_to_move  # Para jogos contra IA, sempre é o turno do jogador quando é vez das brancas
    
    context = {
        'game': game,
        'gs': gs,
        'image_paths': image_paths,
        'player_color': player_color,
        'is_pvp': is_pvp,
        'is_my_turn': is_my_turn,
        'game_over': gs.game_over
    }
    
    return render(request, 'game/game_page.html', context)


@login_required
def make_move_view(request, game_id):
    if request.method == 'POST':
        try:
            game = Game.objects.get(id=game_id)
            
            # Carrega o estado do jogo primeiro
            game_state_dict = json.loads(game.board_state)
            gs = ChessEngine.GameState()
            gs.__dict__.update(game_state_dict)
            
            # Verifica se o usuário é um dos jogadores
            if game.game_type == 'pvp':
                if request.user not in [game.white_player, game.black_player]:
                    return JsonResponse({'status': 'error', 'message': 'Você não é um jogador desta partida.'}, status=403)
                if not game.is_player_turn(request.user):
                    return JsonResponse({'status': 'error', 'message': 'Não é o seu turno.'}, status=400)
            else:
                if request.user != game.white_player:
                    return JsonResponse({'status': 'error', 'message': 'Você não é um jogador desta partida.'}, status=403)
                if not gs.white_to_move:
                    return JsonResponse({'status': 'error', 'message': 'Não é o seu turno.'}, status=400)

            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
            
            start_pos = tuple(data.get('start'))
            end_pos = tuple(data.get('end'))
            promotion_piece = data.get('promotion_piece', 'Q')
            
            # Determina a cor do jogador
            player_color = game.get_player_color(request.user) if game.game_type == 'pvp' else 'w'
            # As coordenadas já vêm corretas do frontend

            # Verifica se é coroação de peão
            is_promotion = gs.is_pawn_promotion(start_pos, end_pos)
            if is_promotion and not promotion_piece:
                return JsonResponse({
                    'status': 'promotion_required',
                    'message': 'Escolha uma peça para coroação.',
                    'start_pos': start_pos,
                    'end_pos': end_pos
                })

            move_was_made = gs.make_move(start_pos, end_pos, promotion_piece)
            
            if not move_was_made:
                return JsonResponse({'status': 'error', 'message': 'Movimento inválido.'}, status=400)
            
            # Atualizar relógios para jogos PvP
            if game.game_type == 'pvp':
                from django.utils import timezone
                current_time = timezone.now()
                
                # Se é o primeiro movimento, inicializar last_move_time
                if not game.last_move_time:
                    game.last_move_time = current_time
                else:
                    # Calcular tempo decorrido desde o último movimento
                    time_elapsed = (current_time - game.last_move_time).total_seconds()
                    
                    # Subtrair tempo decorrido do jogador que acabou de jogar
                    if player_color == 'w':
                        game.white_time_left = max(0, game.white_time_left - int(time_elapsed))
                        # Adicionar incremento
                        game.white_time_left += game.time_increment
                    else:
                        game.black_time_left = max(0, game.black_time_left - int(time_elapsed))
                        # Adicionar incremento
                        game.black_time_left += game.time_increment
                
                # Atualizar timestamp do último movimento
                game.last_move_time = current_time
                
                # Verificar se algum jogador ficou sem tempo
                if game.white_time_left <= 0:
                    gs.game_over = True
                    gs.winner = "Pretas"
                elif game.black_time_left <= 0:
                    gs.game_over = True
                    gs.winner = "Brancas"

            # Salva o histórico de movimentos
            move_history = json.loads(game.move_history) if game.move_history else []
            
            # Adiciona o movimento do jogador
            move_entry = {
                'move_number': len(move_history) + 1,
                'player': 'w' if not gs.white_to_move else 'b',  # Cor de quem fez o movimento
                'from': start_pos,
                'to': end_pos,
                'piece': gs.board[end_pos[0]][end_pos[1]],
                'board_state': [row[:] for row in gs.board],  # Cópia do estado do tabuleiro
                'promotion': promotion_piece if promotion_piece != 'Q' else None
            }
            move_history.append(move_entry)

            # Para jogos contra IA, faz a jogada da IA
            if game.game_type == 'ai' and not gs.game_over:
                ai_move = ChessAI.find_best_move(gs)
                if ai_move:
                    gs.make_move(ai_move[0], ai_move[1])
                    
                    # Adiciona o movimento da IA ao histórico
                    ai_move_entry = {
                        'move_number': len(move_history) + 1,
                        'player': 'w' if not gs.white_to_move else 'b',
                        'from': ai_move[0],
                        'to': ai_move[1],
                        'piece': gs.board[ai_move[1][0]][ai_move[1][1]],
                        'board_state': [row[:] for row in gs.board]
                    }
                    move_history.append(ai_move_entry)
            
            # Salva o histórico atualizado
            game.move_history = json.dumps(move_history)

            # Atualiza o turno no modelo
            game.turn = 'w' if gs.white_to_move else 'b'

            # Se o jogo acabou, atualiza o status no banco de dados
            if gs.game_over:
                if gs.winner == "Brancas":
                    game.status = 'white_win'
                elif gs.winner == "Pretas":
                    game.status = 'black_win'
                else:
                    game.status = 'draw'
                
                # Atualiza ratings apenas para jogos PVP
                if game.game_type == 'pvp':
                    rating_logic.update_ratings(game)

            # Salva o estado final do jogo no banco de dados
            game.board_state = json.dumps(gs.__dict__)
            game.save()

            # Recalcula a visão para o jogador específico
            player_color = game.get_player_color(request.user) if game.game_type == 'pvp' else 'w'
            gs.calculate_vision(player_color)
            vision_board = gs.vision_board
            
            response_data = {
                'status': 'success',
                'vision_board': vision_board,
                'is_game_over': gs.game_over,
                'winner': gs.winner,
                'turn': game.turn
            }
            
            # Adicionar informações dos relógios para jogos PvP
            if game.game_type == 'pvp':
                response_data.update({
                    'white_time_left': game.white_time_left,
                    'black_time_left': game.black_time_left,
                    'time_increment': game.time_increment
                })
            
            return JsonResponse(response_data)

        except Game.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Jogo não encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Requisição inválida'}, status=400)

@login_required
def game_history_view(request, game_id):
    """Retorna o histórico de movimentos de uma partida finalizada"""
    try:
        game = Game.objects.get(id=game_id)
        
        # Verificar se o usuário é um dos jogadores
        if request.user not in [game.white_player, game.black_player]:
            return JsonResponse({'error': 'Você não é um jogador desta partida.'}, status=403)
        
        # Só permitir acesso ao histórico se o jogo terminou
        if game.status == 'ongoing':
            return JsonResponse({'error': 'O histórico só está disponível após o fim da partida.'}, status=400)
        
        # Retornar o histórico de movimentos
        move_history = json.loads(game.move_history) if game.move_history else []
        
        return JsonResponse({
            'status': 'success',
            'move_history': move_history,
            'game_status': game.status
        })
        
    except Game.DoesNotExist:
        return JsonResponse({'error': 'Jogo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def game_data(request, game_id):
    """Retorna dados do jogo incluindo informações dos relógios"""
    try:
        game = Game.objects.get(id=game_id)
        
        # Verificar se o usuário é um jogador da partida
        if not (game.white_player == request.user or game.black_player == request.user):
            return JsonResponse({'error': 'Você não é um jogador desta partida.'}, status=403)
        
        return JsonResponse({
            'status': 'success',
            'game_data': {
                'white_time_left': game.white_time_left,
                'black_time_left': game.black_time_left,
                'time_increment': game.time_increment,
                'turn': game.turn,
                'last_move_time': game.last_move_time.isoformat() if game.last_move_time else None
            }
        })
        
    except Game.DoesNotExist:
        return JsonResponse({'error': 'Jogo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def my_games_view(request):
    """Lista todas as partidas do usuário (finalizadas e em andamento)"""
    # Busca jogos onde o usuário é um dos jogadores
    games = Game.objects.filter(
        models.Q(white_player=request.user) | models.Q(black_player=request.user)
    ).order_by('-created_at')
    
    context = {
        'games': games
    }
    return render(request, 'game/my_games.html', context)

@login_required
def generate_pgn_view(request, game_id):
    """Gera o PGN de uma partida específica"""
    try:
        game = Game.objects.get(id=game_id)
        
        # Verificar se o usuário é um dos jogadores
        if request.user not in [game.white_player, game.black_player]:
            return JsonResponse({'error': 'Você não é um jogador desta partida.'}, status=403)
        
        # Gerar PGN
        pgn = generate_pgn(game)
        
        if request.GET.get('download') == 'true':
            # Retornar como download
            response = HttpResponse(pgn, content_type='application/x-chess-pgn')
            filename = f"xadrez_torto_partida_{game_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pgn"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            # Retornar como JSON para copiar
            return JsonResponse({
                'status': 'success',
                'pgn': pgn
            })
        
    except Game.DoesNotExist:
        return JsonResponse({'error': 'Jogo não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def generate_pgn(game):
    """Gera o PGN profissional de uma partida"""
    # Cabeçalho PGN
    pgn_lines = []
    pgn_lines.append('[Event "Xadrez Torto Online"]')
    pgn_lines.append(f'[Site "Xadrez Torto"]')
    pgn_lines.append(f'[Date "{game.created_at.strftime("%Y.%m.%d")}"]')
    
    # Determinar número da rodada (baseado no ID do jogo)
    pgn_lines.append(f'[Round "{game.id}"]')
    
    # Nomes dos jogadores
    white_name = game.white_player.username if game.white_player else "IA"
    black_name = game.black_player.username if game.black_player else "IA"
    pgn_lines.append(f'[White "{white_name}"]')
    pgn_lines.append(f'[Black "{black_name}"]')
    
    # Resultado
    if game.status == 'white_win':
        result = "1-0"
    elif game.status == 'black_win':
        result = "0-1"
    elif game.status == 'draw':
        result = "1/2-1/2"
    else:
        result = "*"  # Jogo em andamento
    
    pgn_lines.append(f'[Result "{result}"]')
    
    # Informações adicionais
    if hasattr(game.white_player, 'profile'):
        pgn_lines.append(f'[WhiteElo "{int(game.white_player.profile.rating)}"]')
    if hasattr(game.black_player, 'profile'):
        pgn_lines.append(f'[BlackElo "{int(game.black_player.profile.rating)}"]')
    
    pgn_lines.append('')  # Linha em branco
    
    # Movimentos
    move_history = json.loads(game.move_history) if game.move_history else []
    
    if move_history:
        moves_text = []
        move_number = 1
        
        for i, move in enumerate(move_history):
            # Converter movimento para notação algébrica
            algebraic_move = convert_to_algebraic_notation(move, move_history[:i])
            
            if move['player'] == 'w':
                moves_text.append(f"{move_number}. {algebraic_move}")
            else:
                moves_text.append(algebraic_move)
                move_number += 1
        
        # Quebrar linhas a cada 80 caracteres aproximadamente
        current_line = ""
        for move_text in moves_text:
            if len(current_line + " " + move_text) > 80:
                pgn_lines.append(current_line)
                current_line = move_text
            else:
                if current_line:
                    current_line += " " + move_text
                else:
                    current_line = move_text
        
        if current_line:
            pgn_lines.append(current_line + " " + result)
        else:
            pgn_lines.append(result)
    else:
        pgn_lines.append(result)
    
    return "\n".join(pgn_lines)

def convert_to_algebraic_notation(move, previous_moves):
    """Converte um movimento para notação algébrica padrão"""
    piece = move['piece']
    from_pos = move['from']
    to_pos = move['to']
    
    # Converter posições para notação algébrica
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    from_square = files[from_pos[1]] + str(8 - from_pos[0])
    to_square = files[to_pos[1]] + str(8 - to_pos[0])
    
    # Determinar símbolo da peça
    piece_symbols = {
        'K': 'K', 'Q': 'Q', 'R': 'R', 'B': 'B', 'N': 'N', 'p': ''
    }
    
    piece_type = piece[1]  # Remove a cor (w/b)
    piece_symbol = piece_symbols.get(piece_type, '')
    
    # Para peões, não incluir símbolo da peça
    if piece_type == 'p':
        # Se for captura de peão, incluir a coluna de origem
        if from_pos[1] != to_pos[1]:  # Mudança de coluna indica captura
            notation = f"{files[from_pos[1]]}x{to_square}"
        else:
            notation = to_square
    else:
        # Para outras peças
        notation = f"{piece_symbol}{to_square}"
    
    # Adicionar promoção se houver
    if move.get('promotion'):
        notation += f"={move['promotion']}"
    
    return notation