# src/utils/param_sanitize.py
from __future__ import annotations
from typing import Any, Dict, List

def safe_int(v, default: int) -> int:
    try:
        if v is None: return default
        iv = int(v)
        return iv
    except Exception:
        return default

def safe_float(v, default: float) -> float:
    try:
        if v is None: return default
        fv = float(v)
        return fv
    except Exception:
        return default

def coerce_params(schema: List[Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Field(name,type,default,low,high,options,step,...) şemasına göre
    UI’den gelen None / string değerleri tipine dök, None ise default’a düş,
    aralık dışıysa clamp et.
    """
    out = dict(params or {})
    if not schema:
        return out

    for f in schema:
        name = getattr(f, "name", None) or (isinstance(f, dict) and f.get("name"))
        ftype = getattr(f, "type", None) or (isinstance(f, dict) and f.get("type"))
        default = getattr(f, "default", None) if hasattr(f, "default") else (f.get("default") if isinstance(f, dict) else None)
        low = getattr(f, "low", None) if hasattr(f, "low") else (f.get("low") if isinstance(f, dict) else None)
        high = getattr(f, "high", None) if hasattr(f, "high") else (f.get("high") if isinstance(f, dict) else None)
        options = getattr(f, "options", None) if hasattr(f, "options") else (f.get("options") if isinstance(f, dict) else None)

        val = out.get(name, None)
        if ftype in ("int", int):
            val = safe_int(val, safe_int(default, 0))
            if low is not None:  val = max(val, int(low))
            if high is not None: val = min(val, int(high))
        elif ftype in ("float", float):
            val = safe_float(val, safe_float(default, 0.0))
            if low is not None:  val = max(val, float(low))
            if high is not None: val = min(val, float(high))
        elif ftype in ("bool", bool):
            val = bool(default) if val is None else bool(val)
        elif ftype in ("str", str):
            # options varsa en yakın geçerli değere düş
            if val is None: val = default
            if options and val not in options:
                val = default if default in options else options[0]
        else:
            # bilinmeyen tip: default’a düş
            if val is None: val = default

        out[name] = val

    # Yaygın özel kural: fast <= slow
    f = out.get("fast"); s = out.get("slow")
    if isinstance(f, int) and isinstance(s, int) and f > s:
        out["fast"], out["slow"] = s, f
    return out
