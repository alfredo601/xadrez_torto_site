#!/usr/bin/env python3
"""
Script de diagnóstico para o projeto Xadrez Torto na VPS
Execute este script para verificar a configuração do ambiente
"""

import os
import sys
import subprocess
import psycopg2
import redis
from pathlib import Path

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="INFO"):
    color = Colors.GREEN if status == "OK" else Colors.RED if status == "ERROR" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.ENDC} {message}")

def check_file_exists(filepath, description):
    """Verifica se um arquivo existe"""
    if os.path.exists(filepath):
        print_status(f"{description}: {filepath}", "OK")
        return True
    else:
        print_status(f"{description} não encontrado: {filepath}", "ERROR")
        return False

def check_environment_variables():
    """Verifica variáveis de ambiente"""
    print(f"\n{Colors.BOLD}=== Verificando Variáveis de Ambiente ==={Colors.ENDC}")
    
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    # Tentar carregar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_status("python-dotenv carregado", "OK")
    except ImportError:
        print_status("python-dotenv não instalado", "WARNING")
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mascarar valores sensíveis
            if 'SECRET_KEY' in var or 'PASSWORD' in var:
                display_value = value[:10] + "..."
            else:
                display_value = value
            print_status(f"{var}: {display_value}", "OK")
        else:
            print_status(f"{var} não definida", "ERROR")

def check_database_connection():
    """Verifica conexão com PostgreSQL"""
    print(f"\n{Colors.BOLD}=== Verificando Conexão com Banco de Dados ==={Colors.ENDC}")
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print_status("DATABASE_URL não definida", "ERROR")
        return False
    
    try:
        # Parse da URL do banco
        import dj_database_url
        db_config = dj_database_url.parse(database_url)
        
        # Tentar conectar
        conn = psycopg2.connect(
            host=db_config.get('HOST', 'localhost'),
            database=db_config.get('NAME'),
            user=db_config.get('USER'),
            password=db_config.get('PASSWORD'),
            port=db_config.get('PORT', 5432)
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        print_status(f"PostgreSQL conectado: {version[:50]}...", "OK")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print_status(f"Erro na conexão com PostgreSQL: {str(e)}", "ERROR")
        return False

def check_redis_connection():
    """Verifica conexão com Redis"""
    print(f"\n{Colors.BOLD}=== Verificando Conexão com Redis ==={Colors.ENDC}")
    
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url:
        print_status("REDIS_URL não definida", "ERROR")
        return False
    
    try:
        r = redis.from_url(redis_url)
        r.ping()
        info = r.info()
        print_status(f"Redis conectado: versão {info['redis_version']}", "OK")
        return True
    except Exception as e:
        print_status(f"Erro na conexão com Redis: {str(e)}", "ERROR")
        return False

def check_django_configuration():
    """Verifica configuração do Django"""
    print(f"\n{Colors.BOLD}=== Verificando Configuração do Django ==={Colors.ENDC}")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xadrez_torto.settings')
        import django
        django.setup()
        
        from django.conf import settings
        from django.core.management import execute_from_command_line
        
        print_status(f"Django versão: {django.get_version()}", "OK")
        print_status(f"DEBUG: {settings.DEBUG}", "OK")
        print_status(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}", "OK")
        
        # Verificar se consegue fazer check
        try:
            from django.core.management.commands.check import Command
            command = Command()
            command.check()
            print_status("Django check passou", "OK")
        except Exception as e:
            print_status(f"Django check falhou: {str(e)}", "ERROR")
        
        return True
    except Exception as e:
        print_status(f"Erro na configuração do Django: {str(e)}", "ERROR")
        return False

def check_system_services():
    """Verifica serviços do sistema"""
    print(f"\n{Colors.BOLD}=== Verificando Serviços do Sistema ==={Colors.ENDC}")
    
    services = ['postgresql', 'redis-server', 'nginx']
    
    for service in services:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip() == 'active':
                print_status(f"{service} está rodando", "OK")
            else:
                print_status(f"{service} não está rodando", "WARNING")
        except Exception as e:
            print_status(f"Erro ao verificar {service}: {str(e)}", "ERROR")

def check_files_and_directories():
    """Verifica arquivos e diretórios importantes"""
    print(f"\n{Colors.BOLD}=== Verificando Arquivos e Diretórios ==={Colors.ENDC}")
    
    files_to_check = [
        ('manage.py', 'Script de gerenciamento do Django'),
        ('requirements.txt', 'Arquivo de dependências'),
        ('.env', 'Arquivo de variáveis de ambiente'),
        ('xadrez_torto/settings.py', 'Configurações do Django'),
        ('xadrez_torto/asgi.py', 'Configuração ASGI'),
    ]
    
    for filepath, description in files_to_check:
        check_file_exists(filepath, description)
    
    # Verificar diretórios
    dirs_to_check = [
        ('venv', 'Ambiente virtual'),
        ('static', 'Arquivos estáticos'),
        ('game', 'App principal'),
    ]
    
    for dirpath, description in dirs_to_check:
        if os.path.isdir(dirpath):
            print_status(f"{description}: {dirpath}", "OK")
        else:
            print_status(f"{description} não encontrado: {dirpath}", "WARNING")

def main():
    print(f"{Colors.BOLD}=== Diagnóstico do Xadrez Torto VPS ==={Colors.ENDC}")
    print(f"Python: {sys.version}")
    print(f"Diretório atual: {os.getcwd()}")
    print(f"Usuário: {os.getenv('USER', 'desconhecido')}")
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('manage.py'):
        print_status("Este script deve ser executado na raiz do projeto Django!", "ERROR")
        sys.exit(1)
    
    # Executar verificações
    check_files_and_directories()
    check_environment_variables()
    check_system_services()
    check_database_connection()
    check_redis_connection()
    check_django_configuration()
    
    print(f"\n{Colors.BOLD}=== Diagnóstico Concluído ==={Colors.ENDC}")
    print("\nSe houver erros, consulte o arquivo deploy_vps.md para soluções.")

if __name__ == '__main__':
    main()