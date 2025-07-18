#!/bin/bash

# Script de configuração para VPS Hostinger
# Execute este script após clonar o repositório na VPS

echo "=== Configurando Xadrez Torto na VPS ==="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "manage.py" ]; then
    print_error "Este script deve ser executado na raiz do projeto Django!"
    exit 1
fi

print_status "Verificando dependências do sistema..."

# Verificar se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    print_error "Python3 não está instalado!"
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 não está instalado!"
    exit 1
fi

print_status "Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
else
    print_warning "Ambiente virtual já existe"
fi

print_status "Ativando ambiente virtual..."
source venv/bin/activate

print_status "Atualizando pip..."
pip install --upgrade pip

print_status "Instalando dependências..."
pip install -r requirements.txt

print_status "Criando arquivo .env..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Configurações do Django
SECRET_KEY='0(k7hkpo97si3-ytg&$pw1-t1vbj-$fnlw$2r!p+mv1*25z5s7'
DEBUG=False
DJANGO_SETTINGS_MODULE='xadrez_torto.settings'

# Configurações do Banco de Dados PostgreSQL
DATABASE_URL='postgres://xadrezuser:Gr4v3!R0cKb@nd#2025@localhost/xadrezdb'

# Configurações do Redis
REDIS_URL='redis://127.0.0.1:6379/1'

# Configurações do Servidor
PORT=8000
EOF
    print_status "Arquivo .env criado com sucesso!"
else
    print_warning "Arquivo .env já existe"
fi

print_status "Verificando serviços..."

# Verificar PostgreSQL
if systemctl is-active --quiet postgresql; then
    print_status "PostgreSQL está rodando"
else
    print_warning "PostgreSQL não está rodando. Tentando iniciar..."
    sudo systemctl start postgresql
    if systemctl is-active --quiet postgresql; then
        print_status "PostgreSQL iniciado com sucesso"
    else
        print_error "Falha ao iniciar PostgreSQL"
    fi
fi

# Verificar Redis
if systemctl is-active --quiet redis-server; then
    print_status "Redis está rodando"
else
    print_warning "Redis não está rodando. Tentando iniciar..."
    sudo systemctl start redis-server
    if systemctl is-active --quiet redis-server; then
        print_status "Redis iniciado com sucesso"
    else
        print_error "Falha ao iniciar Redis"
    fi
fi

print_status "Testando conexão com banco de dados..."
if python manage.py check --database default; then
    print_status "Conexão com banco de dados OK"
else
    print_error "Falha na conexão com banco de dados"
    print_warning "Verifique se o PostgreSQL está rodando e as credenciais estão corretas"
fi

print_status "Executando migrações..."
if python manage.py migrate; then
    print_status "Migrações executadas com sucesso"
else
    print_error "Falha ao executar migrações"
    exit 1
fi

print_status "Coletando arquivos estáticos..."
if python manage.py collectstatic --noinput; then
    print_status "Arquivos estáticos coletados com sucesso"
else
    print_error "Falha ao coletar arquivos estáticos"
fi

print_status "Testando servidor..."
echo "Iniciando servidor de teste por 10 segundos..."
timeout 10s python manage.py runserver 0.0.0.0:8000 &
SERVER_PID=$!
sleep 5

if kill -0 $SERVER_PID 2>/dev/null; then
    print_status "Servidor está funcionando!"
    kill $SERVER_PID
else
    print_error "Falha ao iniciar servidor"
fi

print_status "=== Configuração concluída! ==="
echo ""
echo "Próximos passos:"
echo "1. Criar superusuário: python manage.py createsuperuser"
echo "2. Testar o servidor: python manage.py runserver 0.0.0.0:8000"
echo "3. Configurar Nginx e systemd (veja deploy_vps.md)"
echo ""
echo "Para acessar o projeto:"
echo "http://82.25.65.2:8000"
echo ""
print_status "Configuração finalizada!"