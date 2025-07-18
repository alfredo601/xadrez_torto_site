# Guia de Deploy na VPS Hostinger

## Passos para configurar o projeto na VPS

### 1. Conectar na VPS e clonar o projeto
```bash
ssh alfredo@82.25.65.2
cd ~
git clone https://github.com/alfredo601/xadrez_torto_site.git
cd xadrez_torto_site
```

### 2. Criar e ativar ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
pip install python-dotenv  # Para carregar variáveis de ambiente
```

### 4. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```bash
nano .env
```

Adicione o seguinte conteúdo:
```
SECRET_KEY='0(k7hkpo97si3-ytg&$pw1-t1vbj-$fnlw$2r!p+mv1*25z5s7'
DEBUG=False
DJANGO_SETTINGS_MODULE='xadrez_torto.settings'
DATABASE_URL='postgres://xadrezuser:Gr4v3!R0cKb@nd#2025@localhost/xadrezdb'
REDIS_URL='redis://127.0.0.1:6379/1'
```

### 5. Configurar PostgreSQL
Verifique se o PostgreSQL está rodando:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql  # Se não estiver rodando
```

### 6. Configurar Redis
Instalar e configurar Redis:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 7. Executar migrações
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 8. Criar superusuário
```bash
python manage.py createsuperuser
```

### 9. Testar o servidor
```bash
python manage.py runserver 0.0.0.0:8000
```

### 10. Configurar Nginx e Gunicorn (Produção)

#### Instalar Nginx:
```bash
sudo apt install nginx
```

#### Criar arquivo de configuração do Nginx:
```bash
sudo nano /etc/nginx/sites-available/xadrez_torto
```

Conteúdo:
```nginx
server {
    listen 80;
    server_name 82.25.65.2 xadreztorto.shop www.xadreztorto.shop;

    location /static/ {
        alias /home/alfredo/xadrez_torto_site/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Ativar o site:
```bash
sudo ln -s /etc/nginx/sites-available/xadrez_torto /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Criar serviço systemd para Daphne:
```bash
sudo nano /etc/systemd/system/xadrez_torto.service
```

Conteúdo:
```ini
[Unit]
Description=Xadrez Torto Django App
After=network.target

[Service]
User=alfredo
Group=alfredo
WorkingDirectory=/home/alfredo/xadrez_torto_site
EnvironmentFile=/home/alfredo/xadrez_torto_site/.env
ExecStart=/home/alfredo/xadrez_torto_site/venv/bin/daphne -b 0.0.0.0 -p 8000 xadrez_torto.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Iniciar o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl start xadrez_torto
sudo systemctl enable xadrez_torto
sudo systemctl status xadrez_torto
```

## Troubleshooting

### Se o erro de DATABASE_URL persistir:
1. Verifique se o arquivo `.env` existe e tem as variáveis corretas
2. Instale python-dotenv: `pip install python-dotenv`
3. Verifique se o PostgreSQL está rodando: `sudo systemctl status postgresql`
4. Teste a conexão com o banco: `psql -h localhost -U xadrezuser -d xadrezdb`

### Verificar logs:
```bash
# Logs do Django
sudo journalctl -u xadrez_torto -f

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

### Comandos úteis:
```bash
# Reiniciar serviços
sudo systemctl restart xadrez_torto
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart redis-server

# Verificar status
sudo systemctl status xadrez_torto
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
```