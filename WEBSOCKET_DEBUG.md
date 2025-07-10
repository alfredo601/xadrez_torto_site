# Guia de Resolução - Problemas com WebSockets em Produção

## Problemas Identificados e Soluções

### 1. Configurações de Domínio
✅ **CORRIGIDO**: Adicionados os domínios corretos no `settings.py`:
- `ALLOWED_HOSTS` agora inclui `www.xadreztorto.shop` e `xadreztorto.shop`
- `CSRF_TRUSTED_ORIGINS` atualizado para ambas as variações do domínio

### 2. Logs de Debug Adicionados
✅ **IMPLEMENTADO**: Sistema de logging para debug:
- Logs no consumer para rastrear usuários online
- Logs no middleware para verificar cache
- Logs no frontend (console do navegador)

### 3. Arquivo requirements.txt Corrigido
✅ **CORRIGIDO**: Arquivo estava com codificação incorreta, agora está limpo

### 4. Melhorias no Frontend
✅ **IMPLEMENTADO**: 
- Correção na detecção de protocolo WebSocket (https: vs wss:)
- Logs detalhados no console do navegador
- Melhor tratamento de erros de conexão

## Configurações Necessárias no Render

### Variáveis de Ambiente
Certifique-se de que estas variáveis estão configuradas no Render:

```bash
# Para usar Redis (recomendado para produção)
REDIS_URL=redis://seu-redis-url

# URL do banco de dados
DATABASE_URL=postgresql://...

# Configurações Django
DJANGO_SETTINGS_MODULE=xadrez_torto.settings
```

### Comando de Build
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

### Comando de Start
```bash
daphne -b 0.0.0.0 -p $PORT xadrez_torto.asgi:application
```

## Como Debuggar

### 1. Verificar Logs do Servidor
No painel do Render, verifique os logs para:
- Erros de conexão WebSocket
- Mensagens de debug dos consumers
- Problemas de autenticação

### 2. Verificar Console do Navegador
Abra o DevTools (F12) e verifique:
- URL de conexão WebSocket sendo usada
- Erros de conexão
- Mensagens de debug

### 3. Testar Localmente
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar com Daphne (mesmo servidor de produção)
daphne -b 127.0.0.1 -p 8000 xadrez_torto.asgi:application
```

## Possíveis Problemas Restantes

### 1. Proxy/Load Balancer do Render
O Render pode estar bloqueando conexões WebSocket. Soluções:
- Verificar se o plano suporta WebSockets
- Contatar suporte do Render se necessário

### 2. Cache em Produção
Se usando InMemoryCache, os dados podem não persistir entre reinicializações.
Solução: Configurar Redis como mostrado acima.

### 3. Timeout de Conexão
WebSockets podem ter timeout em produção.
Solução: Implementar heartbeat/ping-pong.

## Próximos Passos

1. **Deploy das alterações** no GitHub
2. **Verificar logs** no Render após deploy
3. **Testar conexão** WebSocket no site
4. **Verificar console** do navegador para erros
5. **Configurar Redis** se ainda não estiver configurado

## Comandos Úteis para Debug

```python
# No shell do Django (manage.py shell)
from django.core.cache import cache
from django.contrib.auth.models import User

# Verificar usuários no cache
for user in User.objects.all():
    online = cache.get(f'seen_{user.username}')
    print(f'{user.username}: {"Online" if online else "Offline"}')

# Limpar cache
cache.clear()
```

## Contato
Se o problema persistir após essas correções, verifique:
1. Logs detalhados no Render
2. Configurações de rede do provedor
3. Limitações do plano gratuito do Render