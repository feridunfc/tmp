from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple

@dataclass(frozen=True)
class OhlcvSchema:
    required: Tuple[str, ...] = ("Open","High","Low","Close","Volume")
    allow_extras: bool = True
