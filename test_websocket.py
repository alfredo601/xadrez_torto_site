#!/usr/bin/env python
"""
Script de teste para verificar configurações WebSocket
Execute com: python test_websocket.py
"""

import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xadrez_torto.settings')
django.setup()

from django.core.cache import cache
from django.contrib.auth.models import User
from game.consumers import get_online_users_data
import asyncio

def test_cache():
    """Testa se o cache está funcionando"""
    print("=== Teste de Cache ===")
    
    # Testar cache básico
    cache.set('test_key', 'test_value', 60)
    value = cache.get('test_key')
    print(f"Cache básico: {'✅ OK' if value == 'test_value' else '❌ ERRO'}")
    
    # Simular usuário online
    test_user = 'test_user'
    cache.set(f'seen_{test_user}', 'online', 300)
    is_online = cache.get(f'seen_{test_user}')
    print(f"Cache de usuário: {'✅ OK' if is_online else '❌ ERRO'}")
    
    cache.delete('test_key')
    cache.delete(f'seen_{test_user}')

def test_database():
    """Testa conexão com banco de dados"""
    print("\n=== Teste de Banco de Dados ===")
    
    try:
        user_count = User.objects.count()
        print(f"Usuários no banco: {user_count} ✅")
        
        # Verificar se há usuários com perfil
        users_with_profile = User.objects.filter(
            is_superuser=False,
            profile__isnull=False
        ).count()
        print(f"Usuários com perfil: {users_with_profile} ✅")
        
    except Exception as e:
        print(f"Erro no banco: {e} ❌")

async def test_online_users():
    """Testa função de usuários online"""
    print("\n=== Teste de Usuários Online ===")
    
    try:
        # Simular alguns usuários online
        users = User.objects.filter(is_superuser=False)[:3]
        for user in users:
            cache.set(f'seen_{user.username}', 'online', 300)
            print(f"Simulando {user.username} online")
        
        # Testar função
        online_users = await get_online_users_data()
        print(f"Usuários online encontrados: {len(online_users)}")
        
        for user in online_users:
            print(f"  - {user['username']} (Rating: {user['rating']})")
            
        # Limpar cache de teste
        for user in users:
            cache.delete(f'seen_{user.username}')
            
    except Exception as e:
        print(f"Erro ao buscar usuários online: {e} ❌")

def test_settings():
    """Verifica configurações importantes"""
    print("\n=== Verificação de Configurações ===")
    
    print(f"DEBUG: {settings.DEBUG}")
    print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'Não configurado')}")
    print(f"ASGI_APPLICATION: {settings.ASGI_APPLICATION}")
    
    # Verificar Channel Layers
    channel_layers = getattr(settings, 'CHANNEL_LAYERS', {})
    backend = channel_layers.get('default', {}).get('BACKEND', 'Não configurado')
    print(f"Channel Layer Backend: {backend}")
    
    # Verificar Redis
    redis_url = os.environ.get('REDIS_URL')
    print(f"Redis URL: {'Configurado' if redis_url else 'Não configurado (usando InMemory)'}")

def main():
    """Executa todos os testes"""
    print("🔍 Iniciando testes de configuração WebSocket...\n")
    
    test_settings()
    test_cache()
    test_database()
    
    # Teste assíncrono
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_online_users())
    loop.close()
    
    print("\n✅ Testes concluídos!")
    print("\n📝 Próximos passos:")
    print("1. Se todos os testes passaram, o problema pode estar na rede/proxy")
    print("2. Verifique os logs do Render após o deploy")
    print("3. Teste a conexão WebSocket no navegador (F12 > Console)")
    print("4. Considere configurar Redis se ainda não estiver configurado")

if __name__ == '__main__':
    main()