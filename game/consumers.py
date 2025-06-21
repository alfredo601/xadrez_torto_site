# Em game/consumers.py

import json
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import Profile, Challenge, Game
from . import ChessEngine

@database_sync_to_async
def get_all_users_with_profiles():
    """
    Busca todos os usuários com seus perfis do banco de dados.
    """
    return list(User.objects.filter(is_superuser=False).select_related('profile').values(
        'username', 'profile__rating'
    ))

async def get_online_users_data():
    """
    Busca os usuários online combinando dados do banco e cache de forma assíncrona.
    """
    from django.core.cache import cache
    
    # Busca todos os usuários do banco de dados
    all_users = await get_all_users_with_profiles()
    
    # Filtra apenas os usuários online usando cache de forma síncrona
    online_users = []
    for user_data in all_users:
        # Usa database_sync_to_async para operações de cache
        is_online = await database_sync_to_async(cache.get)(f'seen_{user_data["username"]}')
        if is_online:
            online_users.append({
                'username': user_data['username'],
                'rating': int(user_data['profile__rating'])
            })
    
    return online_users

class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'presence'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.broadcast_user_list()

    async def disconnect(self, close_code):
        if self.scope["user"].is_authenticated:
            await database_sync_to_async(cache.delete)(f'seen_{self.scope["user"].username}')
        await self.broadcast_user_list()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Processa mensagens recebidas do cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'challenge_user':
                await self.handle_challenge_user(data)
            elif message_type == 'respond_challenge':
                await self.handle_challenge_response(data)
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Erro ao processar mensagem: {str(e)}'
            }))

    async def handle_challenge_user(self, data):
        """Processa desafio enviado para outro usuário"""
        challenged_username = data.get('challenged_username')
        time_control_minutes = data.get('time_control_minutes', 10)
        time_increment_seconds = data.get('time_increment_seconds', 0)
        challenger = self.scope['user']
        
        if not challenger.is_authenticated:
            return
        
        try:
            challenged_user = await database_sync_to_async(User.objects.get)(username=challenged_username)
            
            # Verifica se já existe um desafio pendente
            existing_challenge = await database_sync_to_async(
                Challenge.objects.filter(
                    challenger=challenger,
                    challenged=challenged_user,
                    status='pending'
                ).first
            )()
            
            if existing_challenge:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Você já enviou um desafio para este jogador.'
                }))
                return
            
            # Cria novo desafio com configurações de tempo
            challenge = await database_sync_to_async(Challenge.objects.create)(
                challenger=challenger,
                challenged=challenged_user,
                time_control_minutes=time_control_minutes,
                time_increment_seconds=time_increment_seconds
            )
            
            # Envia notificação para o jogador desafiado
            await self.channel_layer.group_send(
                'presence',
                {
                    'type': 'challenge_notification',
                    'data': {
                        'type': 'challenge_received',
                        'challenge_id': challenge.id,
                        'challenger_username': challenger.username,
                        'challenged_username': challenged_username,
                        'time_info': {
                            'minutes': time_control_minutes,
                            'increment': time_increment_seconds
                        }
                    }
                }
            )
            
            await self.send(text_data=json.dumps({
                'type': 'challenge_sent',
                'message': f'Desafio enviado para {challenged_username}!'
            }))
            
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Usuário não encontrado.'
            }))

    async def handle_challenge_response(self, data):
        """Processa resposta ao desafio"""
        challenge_id = data.get('challenge_id')
        response = data.get('response')  # 'accept' ou 'reject'
        user = self.scope['user']
        
        if not user.is_authenticated:
            return
        
        try:
            challenge = await database_sync_to_async(Challenge.objects.get)(
                id=challenge_id,
                challenged=user,
                status='pending'
            )
            
            if response == 'accept':
                # Aceita o desafio e cria o jogo
                challenge.status = 'accepted'
                await database_sync_to_async(challenge.save)()
                
                # Obtém informações do desafio de forma assíncrona
                @database_sync_to_async
                def get_challenge_info():
                    return {
                        'challenger': challenge.challenger,
                        'challenged': challenge.challenged,
                        'challenger_username': challenge.challenger.username,
                        'challenged_username': challenge.challenged.username,
                        'time_control_minutes': challenge.time_control_minutes,
                        'time_increment_seconds': challenge.time_increment_seconds
                    }
                
                challenge_info = await get_challenge_info()
                
                # Determina cores aleatoriamente
                if random.choice([True, False]):
                    white_player = challenge_info['challenger']
                    black_player = challenge_info['challenged']
                else:
                    white_player = challenge_info['challenged']
                    black_player = challenge_info['challenger']
                
                # Cria o jogo
                @database_sync_to_async
                def create_game_state():
                    game_engine = ChessEngine.GameState()
                    return json.dumps(game_engine.__dict__)
                
                board_state_json = await create_game_state()
                
                # Calcula tempo inicial em segundos
                initial_time_seconds = challenge_info['time_control_minutes'] * 60
                
                game = await database_sync_to_async(Game.objects.create)(
                    white_player=white_player,
                    black_player=black_player,
                    board_state=board_state_json,
                    game_type='pvp',
                    white_time_left=initial_time_seconds,
                    black_time_left=initial_time_seconds,
                    time_increment=challenge_info['time_increment_seconds']
                )
                
                challenge.game = game
                await database_sync_to_async(challenge.save)()
                
                # Notifica ambos os jogadores
                await self.channel_layer.group_send(
                    'presence',
                    {
                        'type': 'game_started',
                        'data': {
                            'type': 'game_started',
                            'game_id': game.id,
                            'white_player': white_player.username,
                            'black_player': black_player.username,
                            'challenger_username': challenge_info['challenger_username'],
                            'challenged_username': challenge_info['challenged_username']
                        }
                    }
                )
                
            else:
                # Rejeita o desafio
                challenge.status = 'rejected'
                await database_sync_to_async(challenge.save)()
                
                # Obtém informações do desafio de forma assíncrona
                @database_sync_to_async
                def get_challenge_usernames():
                    return {
                        'challenger_username': challenge.challenger.username,
                        'challenged_username': challenge.challenged.username
                    }
                
                challenge_usernames = await get_challenge_usernames()
                
                # Notifica o desafiante
                await self.channel_layer.group_send(
                    'presence',
                    {
                        'type': 'challenge_rejected',
                        'data': {
                            'type': 'challenge_rejected',
                            'challenger_username': challenge_usernames['challenger_username'],
                            'challenged_username': challenge_usernames['challenged_username']
                        }
                    }
                )
                
        except Challenge.DoesNotExist:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Desafio não encontrado ou já foi respondido.'
            }))

    async def user_update(self, event):
        # Esta função envia a lista de usuários para o cliente.
        await self.send(text_data=json.dumps(event['data']))

    async def challenge_notification(self, event):
        """Envia notificação de desafio para o usuário específico"""
        data = event['data']
        if data['challenged_username'] == self.scope['user'].username:
            await self.send(text_data=json.dumps(data))

    async def challenge_rejected(self, event):
        """Envia notificação de desafio rejeitado"""
        data = event['data']
        if data['challenger_username'] == self.scope['user'].username:
            await self.send(text_data=json.dumps(data))

    async def game_started(self, event):
        """Envia notificação de jogo iniciado"""
        data = event['data']
        user = self.scope['user']
        if user.username in [data['challenger_username'], data['challenged_username']]:
            await self.send(text_data=json.dumps(data))

    async def broadcast_user_list(self):
        """
        Função auxiliar que busca os dados e os transmite para o grupo.
        """
        users = await get_online_users_data()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_update",
                "data": {"type": "online_users_list", "users": users},
            },
        )
    
    # --- MÉTODO FALTANTE ADICIONADO AQUI ---
    async def user_joined(self, event):
        """
        Este é o "ramal" que atende à chamada 'user_joined' enviada pelo sinal de login.
        Sua única tarefa é acionar a retransmissão da lista de usuários para todos.
        """
        await self.broadcast_user_list()


class PvPGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'pvp_game_{self.game_id}'
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Verificar se o usuário é um jogador neste jogo
        game = await self.get_game()
        if not game:
            await self.close()
            return
            
        # Verificar se o usuário é um dos jogadores
        @database_sync_to_async
        def get_game_players():
            return game.white_player, game.black_player
        
        white_player, black_player = await get_game_players()
        
        if white_player != self.user and black_player != self.user:
            await self.close()
            return
        
        # Juntar-se ao grupo do jogo
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notificar que o jogador se conectou
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'player_connected',
                'user': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        # Sair do grupo do jogo
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        
        # Notificar que o jogador se desconectou
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'player_disconnected',
                'user': self.user.username
            }
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'move_made':
            # Retransmitir a jogada para o outro jogador
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'move_update',
                    'move_data': data.get('move_data'),
                    'sender': self.user.username
                }
            )
        elif message_type == 'offer_rematch':
            # Processar oferta de revanche
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'rematch_offered',
                    'challenger_username': self.user.username,
                    'sender': self.user.username
                }
            )
        elif message_type == 'respond_rematch':
            # Processar resposta à revanche
            accept = data.get('accept', False)
            if accept:
                # Criar nova partida com cores trocadas
                new_game = await self.create_rematch_game()
                if new_game:
                    await self.channel_layer.group_send(
                        self.game_group_name,
                        {
                            'type': 'rematch_accepted',
                            'new_game_id': new_game.id,
                            'sender': self.user.username
                        }
                    )
            else:
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'rematch_declined',
                        'sender': self.user.username
                    }
                )
    
    # Handlers para eventos do grupo
    async def player_connected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_connected',
            'user': event['user']
        }))
    
    async def player_disconnected(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'user': event['user']
        }))
    
    async def move_update(self, event):
        # Não enviar a jogada de volta para quem a fez
        if event['sender'] != self.user.username:
            # Calcular visão específica para este jogador
            game = await self.get_game()
            if game and game.game_type == 'pvp':
                # Importar aqui para evitar problemas de importação circular
                from . import ChessEngine
                import json
                
                # Carregar estado do jogo
                game_state_dict = json.loads(game.board_state)
                gs = ChessEngine.GameState()
                gs.__dict__.update(game_state_dict)
                
                # Calcular visão para este jogador específico
                player_color = await database_sync_to_async(game.get_player_color)(self.user)
                gs.calculate_vision(player_color)
                
                # Enviar dados com visão específica
                move_data = event['move_data'].copy()
                move_data['vision_board'] = gs.vision_board
                
                await self.send(text_data=json.dumps({
                    'type': 'move_update',
                    'move_data': move_data
                }))
            else:
                # Para jogos não-PvP, usar dados originais
                await self.send(text_data=json.dumps({
                    'type': 'move_update',
                    'move_data': event['move_data']
                }))
    
    # Handlers para eventos de revanche
    async def rematch_offered(self, event):
        # Não enviar a oferta de volta para quem a fez
        if event['sender'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'rematch_offered',
                'challenger_username': event['challenger_username']
            }))
    
    async def rematch_accepted(self, event):
        # Enviar para ambos os jogadores para redirecionamento
        await self.send(text_data=json.dumps({
            'type': 'rematch_accepted',
            'new_game_id': event['new_game_id']
        }))
    
    async def rematch_declined(self, event):
        # Não enviar para quem recusou
        if event['sender'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'rematch_declined'
            }))
    
    @database_sync_to_async
    def create_rematch_game(self):
        """Cria uma nova partida com as cores dos jogadores trocadas"""
        try:
            original_game = Game.objects.get(id=self.game_id)
            
            # Trocar as cores dos jogadores
            new_game = Game.objects.create(
                white_player=original_game.black_player,  # Trocar cores
                black_player=original_game.white_player,  # Trocar cores
                game_type='pvp'
            )
            
            return new_game
        except Game.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_game(self):
        try:
            return Game.objects.get(id=self.game_id)
        except Game.DoesNotExist:
            return None