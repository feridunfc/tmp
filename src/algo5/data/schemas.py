from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class OhlcvSchema:
    required: Tuple[str, ...] = ("Open", "High", "Low", "Close", "Volume")
    allow_extras: bool = True
