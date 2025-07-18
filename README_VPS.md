# Xadrez Torto - Deploy na VPS Hostinger

## 🚀 Comandos Rápidos para Deploy

### 1. Conectar na VPS e configurar projeto
```bash
# Conectar na VPS
ssh alfredo@82.25.65.2

# Clonar o projeto (se ainda não foi clonado)
git clone https://github.com/alfredo601/xadrez_torto_site.git
cd xadrez_torto_site

# Executar script de configuração automática
chmod +x setup_vps.sh
./setup_vps.sh
```

### 2. Criar superusuário
```bash
source venv/bin/activate
python manage.py createsuperuser
```

### 3. Testar o servidor
```bash
python manage.py runserver 0.0.0.0:8000
```

### 4. Verificar configuração (se houver problemas)
```bash
python diagnose_vps.py
```

## 🔧 Solução para o Erro de DATABASE_URL

O erro que você está enfrentando é porque as variáveis de ambiente não estão sendo carregadas. Siga estes passos:

### Passo 1: Instalar python-dotenv
```bash
source venv/bin/activate
pip install python-dotenv
```

### Passo 2: Criar arquivo .env
```bash
nano .env
```

Adicione este conteúdo:
```env
SECRET_KEY='0(k7hkpo97si3-ytg&$pw1-t1vbj-$fnlw$2r!p+mv1*25z5s7'
DEBUG=False
DJANGO_SETTINGS_MODULE='xadrez_torto.settings'
DATABASE_URL='postgres://xadrezuser:Gr4v3!R0cKb@nd#2025@localhost/xadrezdb'
REDIS_URL='redis://127.0.0.1:6379/1'
```

### Passo 3: Testar a configuração
```bash
python manage.py check
python manage.py migrate
```

## 🐛 Troubleshooting

### Erro: "settings.DATABASES is improperly configured"
**Solução:**
1. Verifique se o arquivo `.env` existe na raiz do projeto
2. Verifique se `python-dotenv` está instalado
3. Verifique se o PostgreSQL está rodando: `sudo systemctl status postgresql`

### Erro de conexão com PostgreSQL
**Solução:**
```bash
# Iniciar PostgreSQL
sudo systemctl start postgresql

# Testar conexão
psql -h localhost -U xadrezuser -d xadrezdb
```

### Erro de conexão com Redis
**Solução:**
```bash
# Instalar Redis
sudo apt install redis-server

# Iniciar Redis
sudo systemctl start redis-server

# Testar Redis
redis-cli ping
```

## 📁 Estrutura de Arquivos Importantes

```
xadrez_torto_site/
├── .env                 # Variáveis de ambiente (CRIAR)
├── .env.example         # Exemplo de variáveis
├── manage.py            # Script do Django
├── requirements.txt     # Dependências
├── setup_vps.sh         # Script de configuração
├── diagnose_vps.py      # Script de diagnóstico
├── deploy_vps.md        # Guia completo de deploy
└── xadrez_torto/
    ├── settings.py      # Configurações do Django
    └── asgi.py          # Configuração ASGI
```

## 🌐 Configuração de Produção (Nginx + Systemd)

Para configuração completa de produção, consulte o arquivo `deploy_vps.md`.

## 📞 Informações da VPS

- **IP:** 82.25.65.2
- **Usuário:** alfredo
- **Senha:** Sarah@20meses
- **Banco:** xadrezdb
- **Usuário DB:** xadrezuser
- **Senha DB:** Gr4v3!R0cKb@nd#2025

## 🔗 URLs de Acesso

- **Desenvolvimento:** http://82.25.65.2:8000
- **Admin:** http://82.25.65.2:8000/admin
- **Produção:** https://xadreztorto.shop (após configurar Nginx)

---

**Nota:** Mantenha as credenciais seguras e não as compartilhe publicamente!