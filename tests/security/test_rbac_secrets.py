import os
import pytest
from algo5.security.rbac import RBAC, require, set_role
from algo5.security.secrets import get_secret, _to_env_key

def test_rbac_permissions():
    r = RBAC()
    r.set_role("viewer")
    assert r.can("read") and not r.can("execute")
    r.set_role("trader")
    assert r.can("execute")
    with pytest.raises(ValueError):
        r.set_role("ghost")

def test_require_global():
    set_role("viewer")
    with pytest.raises(PermissionError):
        require("execute")
    set_role("admin")
    require("execute")  # no raise

def test_get_secret_env(monkeypatch):
    key = _to_env_key("binance.api_key")
    monkeypatch.setenv(key, "XYZ")
    assert get_secret("binance.api_key") == "XYZ"
