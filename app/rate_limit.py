from slowapi import Limiter
from slowapi.util import get_remote_address

# Single Limiter instance, shared between app/main.py (registration of the
# 429 error handler) and the routes that apply @limiter.limit(...) - the
# slowapi requires it to be the same object in both places.
limiter = Limiter(key_func=get_remote_address)
