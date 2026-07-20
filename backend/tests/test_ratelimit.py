"""Unidad: primitiva allow() del rate limiter (fallback en memoria)."""
from __future__ import annotations

import pytest

from app.core import ratelimit
from app.core.ratelimit import allow, client_ip


class _Headers(dict):
    def get(self, key, default=None):
        return super().get(key.lower(), default)


class _Request:
    def __init__(self, headers=None, host="127.0.0.1"):
        self.headers = _Headers({k.lower(): v for k, v in (headers or {}).items()})
        self.client = type("Client", (), {"host": host})()


@pytest.fixture(autouse=True)
def _force_memory_backend(monkeypatch):
    # Sin Redis en CI: fuerza el camino de memoria de forma determinista.
    monkeypatch.setattr(ratelimit, "_r", None)
    monkeypatch.setattr(ratelimit, "_last_reconnect", ratelimit.time.time())
    ratelimit._mem.clear()
    yield
    ratelimit._mem.clear()


def test_allows_up_to_limit_then_blocks():
    key = "test:ip-a"
    assert all(allow(key, limit=3) for _ in range(3))  # 3 permitidas
    assert allow(key, limit=3) is False                # 4.ª bloqueada


def test_separate_keys_have_independent_counters():
    assert allow("test:ip-b", limit=1) is True
    assert allow("test:ip-b", limit=1) is False
    # otra key no se ve afectada
    assert allow("test:ip-c", limit=1) is True


def test_old_hits_expire_out_of_window():
    key = "test:ip-d"
    # Inserta un hit "viejo" (fuera de la ventana de 60s) manualmente.
    ratelimit._mem[key] = [ratelimit.time.time() - 120]
    # Ese hit viejo no cuenta -> con limit=1 la nueva petición pasa.
    assert allow(key, limit=1) is True


def test_client_ip_prefers_first_forwarded_for_value():
    req = _Request(
        headers={"X-Forwarded-For": "203.0.113.10, 100.64.0.17"},
        host="100.64.0.99",
    )
    assert client_ip(req) == "203.0.113.10"


def test_client_ip_falls_back_to_request_client_host():
    req = _Request(host="100.64.0.17")
    assert client_ip(req) == "100.64.0.17"
