from django.urls import path
from . import views # Importa as views que vamos criar a seguir

urlpatterns = [
    # URL da página inicial
    path('', views.home_view, name='home'),

    # URLs de autenticação
    path('cadastro/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- NOVAS URLS ABAIXO ---
    path('new_game/', views.create_game_view, name='create_game'),
    path('game/<int:game_id>/', views.game_view, name='game_view'),

    # --- NOVA URL ABAIXO ---
    path('game/<int:game_id>/move/', views.make_move_view, name='make_move'),
    path('game/<int:game_id>/history/', views.game_history_view, name='game_history'),
    
    # URLs para PGN e histórico de partidas
    path('my-games/', views.my_games_view, name='my_games'),
    path('game/<int:game_id>/pgn/', views.generate_pgn_view, name='generate_pgn'),
    path('game/<int:game_id>/data/', views.game_data, name='game_data'),
]