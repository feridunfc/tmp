from __future__ import annotations
from pathlib import Path
import hashlib, hmac
def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
def hmac_sha256(path: str | Path, secret: str) -> str:
    key = secret.encode('utf-8'); hm = hmac.new(key, digestmod=hashlib.sha256)
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hm.update(chunk)
    return hm.hexdigest()
