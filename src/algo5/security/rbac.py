from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Iterable

DEFAULT_ROLES: Dict[str, set[str]] = {
    "viewer": {"read"},
    "trader": {"read", "execute"},
    "admin":  {"read", "execute", "configure", "manage_users"},
}

@dataclass
class RBAC:
    roles: Dict[str, set[str]] = field(default_factory=lambda: {k:set(v) for k,v in DEFAULT_ROLES.items()})
    current_role: str = "viewer"

    def set_role(self, role: str) -> None:
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}")
        self.current_role = role

    def can(self, action: str) -> bool:
        perms = self.roles.get(self.current_role, set())
        return action in perms

    def require(self, action: str) -> None:
        if not self.can(action):
            raise PermissionError(f"Role '{self.current_role}' lacks '{action}' permission.")

# Convenience singleton for quick use in UI
_GLOBAL = RBAC()

def set_role(role: str) -> None:
    _GLOBAL.set_role(role)

def require(action: str) -> None:
    _GLOBAL.require(action)
