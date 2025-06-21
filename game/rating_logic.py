# Em game/rating_logic.py

import glicko2
from .models import Game

def update_ratings(game_instance):
    """
    Calcula e atualiza os ratings dos jogadores com base no resultado de uma partida.
    """
    # Determina quem foi o vencedor e o perdedor
    if game_instance.status == 'white_win':
        winner = game_instance.white_player
        loser = game_instance.black_player
        winner_score = 1.0 # Vitória vale 1.0
        loser_score = 0.0
    elif game_instance.status == 'black_win':
        winner = game_instance.black_player
        loser = game_instance.white_player
        winner_score = 1.0
        loser_score = 0.0
    # Por enquanto, não vamos calcular o rating para empates.
    else:
        return

    # Garante que a partida foi entre dois jogadores humanos (não contra a IA)
    if not winner or not loser:
        return

    # Cria objetos Player do glicko2 para cada jogador
    player_winner = glicko2.Player(rating=winner.profile.rating, rd=winner.profile.rd, vol=winner.profile.vol)
    player_loser = glicko2.Player(rating=loser.profile.rating, rd=loser.profile.rd, vol=loser.profile.vol)

    # Atualiza os ratings usando o método update_player
    # Para o vencedor: jogou contra o perdedor e venceu (score = 1)
    player_winner.update_player([loser.profile.rating], [loser.profile.rd], [winner_score])
    
    # Para o perdedor: jogou contra o vencedor e perdeu (score = 0)
    player_loser.update_player([winner.profile.rating], [winner.profile.rd], [loser_score])

    # Atualiza o perfil do vencedor com os novos valores e salva no banco de dados
    winner.profile.rating = player_winner.rating
    winner.profile.rd = player_winner.rd
    winner.profile.vol = player_winner.vol
    winner.profile.save()

    # Atualiza o perfil do perdedor
    loser.profile.rating = player_loser.rating
    loser.profile.rd = player_loser.rd
    loser.profile.vol = player_loser.vol
    loser.profile.save()