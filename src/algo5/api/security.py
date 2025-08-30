from __future__ import annotations
class AuthError(Exception): ...
def require_api_key(expected: str, provided: str | None) -> None:
    if expected and (provided != expected): raise AuthError("invalid api key")
