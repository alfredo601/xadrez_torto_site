from django.contrib import admin
from .models import Profile # Importa nosso modelo Profile

# Registra o modelo Profile no painel de administração
admin.site.register(Profile)