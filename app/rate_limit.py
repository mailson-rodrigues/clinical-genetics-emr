from slowapi import Limiter
from slowapi.util import get_remote_address

# Instância única de Limiter, compartilhada entre app/main.py (registro do
# handler de erro 429) e as rotas que aplicam @limiter.limit(...) - o
# slowapi exige que seja o mesmo objeto nos dois lugares.
limiter = Limiter(key_func=get_remote_address)
