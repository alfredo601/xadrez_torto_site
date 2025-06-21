from django.db import models
from django.contrib.auth.models import User # Vamos usar o sistema de usuários do Django
import json # Usaremos para armazenar o estado do tabuleiro

class Game(models.Model):
    """ Este modelo representa uma única partida de Xadrez Torto. """

    # Jogadores. O ForeignKey cria uma ligação com o modelo de usuário do Django.
    # related_name nos permite encontrar todas as partidas de um usuário.
    # models.SET_NULL significa que se um usuário for deletado, o jogo não é deletado,
    # mas o campo do jogador fica vazio (nulo).
    white_player = models.ForeignKey(User, related_name='games_as_white', on_delete=models.SET_NULL, null=True)
    black_player = models.ForeignKey(User, related_name='games_as_black', on_delete=models.SET_NULL, null=True)

    # Usamos um TextField para armazenar o estado do tabuleiro em formato de texto (JSON).
    # Isso nos dá flexibilidade para guardar nosso tabuleiro [[...], [...], ...].
    board_state = models.TextField(default='{}')
    
    # Histórico completo de movimentos para reprodução da partida
    move_history = models.TextField(default='[]')

    # De quem é a vez? 'w' para brancas, 'b' para pretas.
    turn = models.CharField(max_length=1, default='w')

    # Status da partida
    STATUS_CHOICES = [
        ('ongoing', 'Em Andamento'),
        ('white_win', 'Vitória das Brancas'),
        ('black_win', 'Vitória das Pretas'),
        ('draw', 'Empate'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ongoing')

    # Tipo de jogo: contra IA ou PVP
    GAME_TYPE_CHOICES = [
        ('ai', 'Contra IA'),
        ('pvp', 'Jogador vs Jogador'),
    ]
    game_type = models.CharField(max_length=3, choices=GAME_TYPE_CHOICES, default='ai')
    
    # Controle de tempo para jogos PvP
    white_time_left = models.IntegerField(null=True, blank=True, help_text="Tempo restante das brancas em segundos")
    black_time_left = models.IntegerField(null=True, blank=True, help_text="Tempo restante das pretas em segundos")
    time_increment = models.IntegerField(default=0, help_text="Incremento em segundos por lance")
    last_move_time = models.DateTimeField(null=True, blank=True, help_text="Timestamp do último movimento")

    # Datas de criação e última atualização.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Partida #{self.id} - {self.white_player} vs {self.black_player}"

    def get_player_color(self, user):
        """Retorna a cor do jogador ('w' ou 'b') ou None se não for jogador desta partida"""
        if self.white_player == user:
            return 'w'
        elif self.black_player == user:
            return 'b'
        return None

    def is_player_turn(self, user):
        """Verifica se é a vez do jogador"""
        player_color = self.get_player_color(user)
        if not player_color:
            return False
        return (self.turn == 'w' and player_color == 'w') or (self.turn == 'b' and player_color == 'b')

class Challenge(models.Model):
    """Modelo para representar desafios entre jogadores"""
    challenger = models.ForeignKey(User, related_name='sent_challenges', on_delete=models.CASCADE)
    challenged = models.ForeignKey(User, related_name='received_challenges', on_delete=models.CASCADE)
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('accepted', 'Aceito'),
        ('rejected', 'Rejeitado'),
        ('expired', 'Expirado'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Configurações de tempo para o jogo
    time_control_minutes = models.IntegerField(default=10, help_text="Tempo inicial em minutos para cada jogador")
    time_increment_seconds = models.IntegerField(default=0, help_text="Incremento em segundos por lance")
    
    # Referência ao jogo criado quando o desafio é aceito
    game = models.OneToOneField(Game, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Desafio de {self.challenger.username} para {self.challenged.username} - {self.status}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # O rating agora é FloatField para maior precisão.
    rating = models.FloatField(default=1500.0)

    # Novos campos para o Glicko-2 com valores padrão recomendados.
    rd = models.FloatField(default=350.0)
    vol = models.FloatField(default=0.06)

    def __str__(self):
        return f'Perfil de {self.user.username} (Rating: {int(self.rating)})'