"""Security primitives: RBAC & Secrets (env-based)."""
__all__ = ["RBAC", "require", "get_secret"]
from .rbac import RBAC, require
from .secrets import get_secret
