
from __future__ import annotations
import random

class EpsilonGreedy:
    def __init__(self, arms: list[str], eps: float = 0.1, seed: int = 42):
        self.arms = arms
        self.eps = eps
        random.seed(seed)
        self.cnt = {a: 0 for a in arms}
        self.sum = {a: 0.0 for a in arms}
    def select(self) -> str:
        if random.random() < self.eps:
            return random.choice(self.arms)
        avg = {a: (self.sum[a] / self.cnt[a]) if self.cnt[a] else 0.0 for a in self.arms}
        return max(self.arms, key=lambda a: avg[a])
    def update(self, arm: str, reward: float) -> None:
        self.cnt[arm] += 1
        self.sum[arm] += float(reward)
