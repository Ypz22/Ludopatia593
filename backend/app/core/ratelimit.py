"""
Rate limiting por ventana fija sobre Redis (defensa fuerza bruta / abuso).
Si Redis no está disponible, degrada a memoria local (best-effort).
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict

import redis

from .config import settings

logger = logging.getLogger(__name__)


def _connect():
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
        return r
    except Exception:
        return None


_r = _connect()
_mem: dict[str, list[float]] = defaultdict(list)
_last_reconnect = 0.0
_warned_fallback = False


def get_redis():
    """Cliente Redis vivo o None (con reconexión perezosa). Para cache best-effort."""
    global _r, _last_reconnect
    if _r is None and time.time() - _last_reconnect > 5:
        _last_reconnect = time.time()
        _r = _connect()
    return _r


def allow(key: str, limit: int, window_sec: int = 60) -> bool:
    """True si la acción está permitida; False si excede el límite."""
    global _r, _last_reconnect, _warned_fallback
    now = time.time()

    # Reconexión perezosa: si Redis se cayó, reintenta como máximo cada 5s
    # (evita que un fallo transitorio deje el rate limit degradado para siempre).
    if _r is None and now - _last_reconnect > 5:
        _last_reconnect = now
        _r = _connect()

    if _r is not None:
        try:
            pipe = _r.pipeline()
            bucket = f"rl:{key}:{int(now // window_sec)}"
            pipe.incr(bucket)
            pipe.expire(bucket, window_sec)
            count, _ = pipe.execute()
            return int(count) <= limit
        except Exception:
            _r = None  # marca caído -> forzará reconexión perezosa

    # Fallback a memoria (best-effort). En multi-instancia NO es global:
    # avisar una vez fuera de 'dev' para que sea visible en operación.
    if not _warned_fallback and settings.environment != "dev":
        _warned_fallback = True
        logger.warning("rate limit degradado a memoria local: Redis no disponible")
    hits = [t for t in _mem[key] if now - t < window_sec]
    hits.append(now)
    _mem[key] = hits
    return len(hits) <= limit
