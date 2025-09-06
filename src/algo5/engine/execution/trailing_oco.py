from __future__ import annotations
from contextlib import suppress

"""Lightweight trailing-stop + OCO wrapper for ``match_order_on_bar``.
Keeps per-order peak/trough in a module-level dict, decorates the base
matcher to inject trailing behaviour, and cancels OCO siblings after a fill.
The wrapper is lenient: it passes through *args/**kwargs to the original
matcher and only uses kwargs ``o``, ``h``, ``low`` (or ``l``) and ``c`` if present.
"""

_TRAIL_STATE: dict[str, dict[str, float]] = {}  # order_id -> {peak|trough}


def _oid(order) -> str:
    return str(getattr(order, "id", repr(order)))


def _side(order) -> str:
    return str(getattr(order, "side", "SELL")).upper()


def _update_anchor(order, high: float, low: float) -> None:
    st = _TRAIL_STATE.setdefault(_oid(order), {})
    s = _side(order)
    if "SELL" in s or "LONG" in s:  # long exit
        st["peak"] = max(high, st.get("peak", high))
    else:  # short exit
        st["trough"] = min(low, st.get("trough", low) if "trough" in st else low)


def _calc_level(order):
    st = _TRAIL_STATE.get(_oid(order), {})
    pct = getattr(order, "trail_pct", None)
    amt = getattr(order, "trail_amount", None)
    s = _side(order)

    if "SELL" in s or "LONG" in s:
        peak = st.get("peak")
        if peak is None:
            return None
        if pct:
            return float(peak) * (1.0 - float(pct))
        if amt:
            return float(peak) - float(amt)
    else:
        trough = st.get("trough")
        if trough is None:
            return None
        if pct:
            return float(trough) * (1.0 + float(pct))
        if amt:
            return float(trough) + float(amt)
    return None


def _try_fill_trailing(order, o: float, high: float, low: float):
    lvl = _calc_level(order)
    if lvl is None:
        return False, None
    s = _side(order)
    if "SELL" in s or "LONG" in s:
        if (o <= lvl) or (low <= lvl):
            return True, float(min(o, lvl))
    else:
        if (o >= lvl) or (high >= lvl):
            return True, float(max(o, lvl))
    return False, None


def wrap_matcher(orig_match):
    """Return a wrapper around ``orig_match`` (match_order_on_bar)."""

    def _wrapped(order, *args, **kwargs):
        # kwargs’tan OHLC çek (bazı çağrılarda low 'l' olarak gelebilir)
        o = kwargs.get("o")
        h = kwargs.get("h")
        low = kwargs.get("low", kwargs.get("l"))
        c = kwargs.get("c")

        # önce orijinal eşleştiriciyi çağır
        res = orig_match(order, *args, **kwargs)

        # trailing stop sadece OHLC mevcutsa kontrol edilir
        if (
            o is not None
            and h is not None
            and low is not None
            and c is not None
            and str(getattr(order, "type", "")).upper() == "TRAILING_STOP"
        ):
            _update_anchor(order, float(h), float(low))
            filled, px = _try_fill_trailing(order, float(o), float(h), float(low))
            if filled:
                with suppress(Exception):
                    res.filled = True
                    res.price = px
                    if getattr(order, "oco_id", None):
                        res.cancel_oco_id = order.oco_id
                return res

        # OCO: vanilla fill olduysa kardeşi iptal ettir
        if getattr(res, "filled", False) and getattr(order, "oco_id", None):
            with suppress(Exception):
                res.cancel_oco_id = order.oco_id
        return res

    return _wrapped
