from __future__ import annotations
import re
_POS = {"good","bull","up","gain","green","beat","accumulate","positive"}
_NEG = {"bad","bear","down","loss","red","miss","sell","negative"}
def simple_sentiment(text: str) -> float:
    toks = re.findall(r"[A-Za-z]+", text.lower())
    if not toks: return 0.0
    pos = sum(1 for t in toks if t in _POS); neg = sum(1 for t in toks if t in _NEG)
    return (pos - neg) / max(1, len(toks))
