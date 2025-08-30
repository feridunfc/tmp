from __future__ import annotations
import os

def _to_env_key(path: str) -> str:
    # "binance.api_key" -> "ALGO5_SECRET__BINANCE__API_KEY"
    parts = [p.strip() for p in path.replace(":", ".").split(".") if p.strip()]
    key = "ALGO5_SECRET__" + "__".join(p.upper() for p in parts)
    return key

def get_secret(path: str, default: str | None = None) -> str | None:
    env_key = _to_env_key(path)
    return os.getenv(env_key, default)
