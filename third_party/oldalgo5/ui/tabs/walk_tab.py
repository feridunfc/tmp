# ui/tabs/walk_tab.py
from __future__ import annotations
import numpy as np

import importlib
import inspect
import math
import types
import traceback
from typing import Any, Dict, Tuple, List

import pandas as pd
import streamlit as st

import time, threading, queue


# ---------- walkforward import (esnek) ----------
def _import_walkforward():
    candidates = (
        "core.backtest.walkforward",
        "src.core.backtest.walkforward",
        "src.core.backtest.walkforward",
        "src.core.backtest.walkforward",
    )
    last_err = None
    for cand in candidates:
        try:
            mod = importlib.import_module(cand)
            fn = (
                getattr(mod, "run_walkforward", None)
                or getattr(mod, "walkforward", None)
                or getattr(mod, "run", None)
            )
            if fn is not None:
                return fn
        except Exception as e:
            last_err = e
    raise ImportError(f"walkforward modülü bulunamadı. Denenen yollar: {candidates}. Son hata: {last_err}")

run_walkforward = _import_walkforward()


# ---------- opsiyonel proje yardımcıları ----------
try:
    from utils.param_sanitize import coerce_params as _proj_coerce, safe_int  # type: ignore
except Exception:
    _proj_coerce = None
    def safe_int(v, fallback=0):
        try:
            return fallback if v is None else int(v)
        except Exception:
            return fallback


# ---------- registry import (esnek) ----------
try:
    from src.strategies.registry import get_registry, get_strategy
except Exception:
    from src.strategies.registry import get_registry, get_strategy  # type: ignore

from ui.components.error_banner import show_error
import ui.services.sdk as sdk  # backtest fn için


# ---------- küçük yardımcılar ----------
def _is_nan(x) -> bool:
    return isinstance(x, float) and math.isnan(x)

def _nan_or_empty_to_none(x):
    if x is None: return None
    if isinstance(x, str) and x.strip() == "": return None
    if _is_nan(x): return None
    return x

def _as_int(x, default: int) -> int:
    x = _nan_or_empty_to_none(x)
    if x is None: return int(default)
    try: return int(float(x))
    except Exception: return int(default)

def _as_float(x, default: float) -> float:
    x = _nan_or_empty_to_none(x)
    if x is None: return float(default)
    try: return float(x)
    except Exception: return float(default)

def _to_py_type(t):
    if t in (int, float, bool, str): return t
    if isinstance(t, str):
        return {"int": int, "float": float, "bool": bool, "str": str}.get(t.lower(), str)
    return str

def _normalize_schema_to_dict(schema) -> dict:
    if callable(schema):
        try: schema = schema()
        except Exception: return {}
    if isinstance(schema, dict):
        out = {}
        for k, v in schema.items():
            if isinstance(v, dict):
                vv = dict(v)
                for kk in ("low","high","min","max","step","default"):
                    if kk in vv: vv[kk] = _nan_or_empty_to_none(vv[kk])
                out[k] = vv
            else:
                out[k] = _nan_or_empty_to_none(v)
        return out
    out = {}
    if isinstance(schema, (list, tuple)):
        for f in schema:
            if hasattr(f, "name"):
                name = getattr(f, "name")
                out[name] = {
                    "type": getattr(f, "type", "str"),
                    "default": _nan_or_empty_to_none(getattr(f, "default", None)),
                    "low": _nan_or_empty_to_none(getattr(f, "low", None)),
                    "high": _nan_or_empty_to_none(getattr(f, "high", None)),
                    "step": _nan_or_empty_to_none(getattr(f, "step", None)),
                    "options": getattr(f, "options", None),
                }
            elif isinstance(f, dict) and "name" in f:
                name = f.get("name")
                d = dict(f); d.pop("name", None)
                for kk in ("low","high","min","max","step","default"):
                    if kk in d: d[kk] = _nan_or_empty_to_none(d[kk])
                out[name] = d
    return out

def _coerce_params_local(schema, raw: dict) -> dict:
    schema = _normalize_schema_to_dict(schema)
    out: Dict[str, Any] = {}
    for name, meta in (schema or {}).items():
        meta = meta or {}
        py = _to_py_type(meta.get("type", "str"))
        val = (raw or {}).get(name, meta.get("default"))
        if val is None:
            low = meta.get("low")
            if py is int: val = _as_int(low, 0)
            elif py is float: val = _as_float(low, 0.0)
            elif py is bool: val = False
            else: val = ""
        try: out[name] = py(val)
        except Exception: out[name] = val
    for k, v in (raw or {}).items():
        out.setdefault(k, v)
    return out

def _coerce_params(schema, raw: dict) -> dict:
    if _proj_coerce is not None:
        try: return _proj_coerce(_normalize_schema_to_dict(schema), raw)
        except Exception: pass
    return _coerce_params_local(schema, raw)

def _safe_default(field, fallback_int=0, fallback_float=0.0, fallback_str=""):
    if hasattr(field, "name"): get = lambda k, d=None: getattr(field, k, d)
    elif isinstance(field, dict): get = lambda k, d=None: field.get(k, d)
    else: return fallback_str
    typ = get("type")
    default = _nan_or_empty_to_none(get("default"))
    if default is None:
        if typ in (int,"int"): default = _as_int(get("low"), fallback_int)
        elif typ in (float,"float"): default = _as_float(get("low"), fallback_float)
        elif typ in (bool,"bool"): default = False
        else: default = fallback_str
    return default

def _guard_range_num(low, high, is_float=False):
    if low is None: low = 0.0 if is_float else 0
    if high is None: high = (low + 1.0) if is_float else (low + 10)
    if is_float:
        mn = _as_float(low, 0.0); mx = _as_float(high, mn + 1.0)
        if not (mx > mn): mx = mn + 1.0
    else:
        mn = _as_int(low, 0); mx = _as_int(high, mn + 10)
        if not (mx > mn): mx = mn + 10
    return mn, mx

def _count_points(lo, hi, step, is_float: bool) -> int:
    try:
        if is_float:
            n = int(math.floor((float(hi) - float(lo)) / float(step))) + 1
        else:
            n = int((int(hi) - int(lo)) // int(step)) + 1
        return max(1, n)
    except Exception:
        return 1

def _cap_step(lo, hi, step, is_float: bool, max_points: int):
    lo2, hi2 = (float(lo), float(hi)) if is_float else (int(lo), int(hi))
    if step is None or (is_float and step <= 0) or (not is_float and int(step) <= 0):
        step = 0.1 if is_float else 1
    cnt = _count_points(lo2, hi2, step, is_float)
    if cnt <= max_points:
        return step
    if is_float:
        span = max(1e-12, hi2 - lo2)
        step = span / max_points
        step = round(step, 3)
        if step <= 0:
            step = 0.001
    else:
        span = max(1, hi2 - lo2)
        step = max(1, math.ceil(span / max_points))
    return step

def _clip_default(v, mn, mx, to_float=False):
    if to_float:
        v = _as_float(v, mn); mn = float(mn); mx = float(mx)
    else:
        v = _as_int(v, mn); mn = int(mn); mx = int(mx)
    if v < mn: v = mn
    if v > mx: v = mx
    return v


# ---------- strateji I/O keşfi ----------
def _resolve_io(strat_obj) -> Tuple[Any, Any]:
    if isinstance(strat_obj, dict):
        return strat_obj.get("prep"), strat_obj.get("gen")
    if inspect.isclass(strat_obj):
        try:
            inst = strat_obj()
            prep = getattr(inst, "prepare", None) or getattr(strat_obj, "prepare", None)
            gen = getattr(inst, "generate_signals", None) or getattr(strat_obj, "generate_signals", None)
            return prep, gen
        except Exception:
            return getattr(strat_obj, "prepare", None), getattr(strat_obj, "generate_signals", None)
    if isinstance(strat_obj, types.ModuleType):
        return getattr(strat_obj, "prepare", None), getattr(strat_obj, "generate_signals", None)
    return getattr(strat_obj, "prepare", None), getattr(strat_obj, "generate_signals", None)

def _filter_kwargs_for_callable(fn, src: dict) -> dict:
    try:
        sig = inspect.signature(fn)
        allowed = set(sig.parameters.keys())
        return {k: v for k, v in (src or {}).items() if isinstance(k, str) and k in allowed}
    except Exception:
        return dict(src or {})


# ---------- parametre formu ----------
def _render_param_form(schema: Any, key_prefix: str = "wf_param_") -> Dict[str, Any]:
    if callable(schema):
        try: schema = schema()
        except Exception: pass

    params: Dict[str, Any] = {}
    if not schema: return params

    if isinstance(schema, list):
        for i, f in enumerate(schema):
            if hasattr(f, "name"):
                name, typ = getattr(f, "name"), getattr(f, "type", "str")
                low, high, step, options = (
                    getattr(f, "low", None), getattr(f, "high", None),
                    getattr(f, "step", None), getattr(f, "options", None)
                )
            elif isinstance(f, dict):
                name, typ = f.get("name"), f.get("type", "str")
                low, high, step, options = f.get("low"), f.get("high"), f.get("step"), f.get("options")
            else:
                continue
            if not name: continue

            k = f"{key_prefix}{name}_{i}"
            typ_str = typ if isinstance(typ, str) else (typ.__name__ if typ in (int,float,bool,str) else "str")
            default_raw = _safe_default(f)

            try:
                if typ_str in ("int", int):
                    mn, mx = _guard_range_num(low, high, is_float=False)
                    stp = _as_int(step, 1); stp = 1 if stp <= 0 else stp
                    dv = _clip_default(default_raw, mn, mx, to_float=False)
                    val = st.number_input(name, value=int(dv), min_value=mn, max_value=mx, step=stp, key=k)
                elif typ_str in ("float", float):
                    mn, mx = _guard_range_num(low, high, is_float=True)
                    stp = _as_float(step, 0.1); stp = 0.1 if stp <= 0 else stp
                    dv = _clip_default(default_raw, mn, mx, to_float=True)
                    val = st.number_input(name, value=float(dv), min_value=mn, max_value=mx, step=stp, key=k)
                elif typ_str in ("bool", bool):
                    val = st.checkbox(name, value=bool(default_raw), key=k)
                else:
                    if options and isinstance(options, (list, tuple)) and len(options) > 0:
                        try: idx = options.index(default_raw) if default_raw in options else 0
                        except Exception: idx = 0
                        val = st.selectbox(name, options, index=idx, key=k)
                    else:
                        val = st.text_input(name, value=str(default_raw if default_raw is not None else ""), key=k)
                params[name] = val
            except Exception as e:
                st.error(f"Parametre '{name}' işlenirken hata: {e}")
                params[name] = default_raw

    elif isinstance(schema, dict):
        for i, (name, meta) in enumerate(schema.items()):
            if name is None: continue
            if isinstance(meta, dict):
                typ = meta.get("type", "str")
                low = _nan_or_empty_to_none(meta.get("low"))
                high = _nan_or_empty_to_none(meta.get("high"))
                step = _nan_or_empty_to_none(meta.get("step"))
                options = meta.get("options")
                default_raw = _nan_or_empty_to_none(meta.get("default"))
            else:
                typ, low, high, step, options, default_raw = "str", None, None, None, None, _nan_or_empty_to_none(meta)

            k = f"{key_prefix}{name}_{i}"
            typ_str = typ if isinstance(typ, str) else (typ.__name__ if typ in (int,float,bool,str) else "str")

            try:
                if typ_str in ("int", int):
                    mn, mx = _guard_range_num(low, high, is_float=False)
                    stp = _as_int(step, 1); stp = 1 if stp <= 0 else stp
                    dv = _clip_default(default_raw, mn, mx, to_float=False)
                    val = st.number_input(name, value=int(dv), min_value=mn, max_value=mx, step=stp, key=k)
                elif typ_str in ("float", float):
                    mn, mx = _guard_range_num(low, high, is_float=True)
                    stp = _as_float(step, 0.1); stp = 0.1 if stp <= 0 else stp
                    dv = _clip_default(default_raw, mn, mx, to_float=True)
                    val = st.number_input(name, value=float(dv), min_value=mn, max_value=mx, step=stp, key=k)
                elif typ_str in ("bool", bool):
                    val = st.checkbox(name, value=bool(default_raw), key=k)
                else:
                    if options and isinstance(options, (list, tuple)) and len(options) > 0:
                        try: idx = options.index(default_raw) if default_raw in options else 0
                        except Exception: idx = 0
                        val = st.selectbox(name, options, index=idx, key=k)
                    else:
                        val = st.text_input(name, value=str(default_raw if default_raw is not None else ""), key=k)
                params[name] = val
            except Exception as e:
                st.error(f"Parametre '{name}' işlenirken hata: {e}")
                params[name] = default_raw

    return params


# ---------- wf köprüsü ----------
def _to_wf_schema(schema) -> dict:
    """
    run_walkforward için grid:
    - sadece sayısal alanlar (int/float)
    - Quick mode açıksa parametre başına nokta sayısı agresif düşürülür
    """
    norm = _normalize_schema_to_dict(schema)
    out = {}
    quick = st.session_state.get("wf_quick_mode", True)
    for name, meta in (norm or {}).items():
        meta = meta or {}
        py = _to_py_type(meta.get("type", "str"))
        if py not in (int, float):
            continue

        is_float = (py is float)
        lo = meta.get("min", meta.get("low"))
        hi = meta.get("max", meta.get("high"))
        mn, mx = _guard_range_num(lo, hi, is_float=is_float)

        raw_step = meta.get("step")
        stp = _as_float(raw_step, 0.1) if is_float else _as_int(raw_step, 1)

        # Quick mode → param başına 2 (float) / 3 (int) nokta hedefi
        points_cap = 2 if (quick and is_float) else (3 if (quick and not is_float) else (7 if is_float else 10))
        stp = _cap_step(mn, mx, stp, is_float, points_cap)

        out[name] = {
            "type": "float" if is_float else "int",
            "min": float(mn) if is_float else int(mn),
            "max": float(mx) if is_float else int(mx),
            "step": float(stp) if is_float else int(stp),
        }
    return out

def _estimate_total_grid(schema_wf: dict) -> int:
    total = 1
    for _, s in (schema_wf or {}).items():
        is_float = s.get("type") == "float"
        total *= _count_points(s["min"], s["max"], s["step"], is_float)
        if total > 10_000_000:
            break
    return int(total)

def _points_for_param(s: dict) -> int:
    lo, hi, step = s["min"], s["max"], s["step"]
    is_float = (s.get("type") == "float")
    return _count_points(lo, hi, step, is_float)

def _shrink_grid(schema_wf: dict, limit: int) -> dict:
    """
    step'leri büyüterek toplam kombinasyonu 'limit' altına indir.
    En yoğun paramdan başlanır.
    """
    s = {k: dict(v) for k, v in (schema_wf or {}).items()}

    def total():
        t = 1
        for v in s.values():
            t *= _points_for_param(v)
            if t > limit * 10:
                break
        return int(t)

    if total() <= limit:
        return s

    guard = 0
    while total() > limit and guard < 5000:
        guard += 1
        key = max(s.keys(), key=lambda k: _points_for_param(s[k]))
        v = s[key]
        is_float = (v.get("type") == "float")
        span = (v["max"] - v["min"])

        if is_float:
            new_step = max(round(v["step"] * 1.8, 6), 0.001)
            if new_step > max(1e-12, span):
                new_step = span
            v["step"] = new_step
        else:
            new_step = max(int(v["step"]) + 1, 1)
            if new_step > max(1, int(span)):
                new_step = max(1, int(span))
            v["step"] = new_step

    return s


def _align_signal(sig: pd.Series, df_like: pd.DataFrame) -> pd.Series:
    """Seri uzunluğu/indeksi df ile eşleşmiyorsa nötr (0) ile toparla."""
    if sig is None:
        return pd.Series(0.0, index=df_like.index, name="signal")
    if not isinstance(sig, pd.Series):
        sig = pd.Series(sig, index=df_like.index[:len(sig)], name="signal")
    # mümkünse reindex
    try:
        sig = sig.reindex(df_like.index)
    except Exception:
        pass
    # baştan doldur / kırp
    if len(sig) < len(df_like):
        pad = len(df_like) - len(sig)
        pad_ser = pd.Series(0.0, index=df_like.index[:pad], name="signal")
        sig = pd.concat([pad_ser, sig.iloc[:len(df_like)-pad]])
        sig.index = df_like.index
    elif len(sig) > len(df_like):
        sig = sig.iloc[-len(df_like):]
        sig.index = df_like.index
    sig.name = "signal"
    return sig


def _wf_call_dynamic(
    run_walkforward_func,
    df,
    schema,
    params,
    prep_fn,
    gen_fn,
    strat_obj,
    *,
    n_splits,
    min_train,
    embargo,
    commission,
    slippage,
    capital,
    backtest_fn,
    schema_wf_override=None,
):
    """run_walkforward(strategy_cls=wrapper, df=df, schema=...) şeklinde çağrıyı köprüler."""
    sig = inspect.signature(run_walkforward_func)
    names = set(sig.parameters.keys())

    schema_wf = schema_wf_override or _to_wf_schema(schema)

    # fold başına instance/canlı durum
    _state = {"inst": None, "trained": False}

    def _make_instance(p: dict):
        # class/callable ise dene; modül/instance ise olduğu gibi kullan
        if inspect.isclass(strat_obj) or callable(strat_obj):
            try:
                return strat_obj(**(p or {}))
            except TypeError:
                try:
                    return strat_obj()
                except Exception:
                    return strat_obj
        return strat_obj

    def _prepare_bridge(d, p=None, **kw):
        p = {str(k): v for k, v in (p or {}).items() if k is not False}
        inst = _state.get("inst")
        # 1) instance.prepare
        if inst is not None and hasattr(inst, "prepare") and callable(inst.prepare):
            try:
                return inst.prepare(d, **_filter_kwargs_for_callable(inst.prepare, p))
            except TypeError:
                try:
                    return inst.prepare(d, p)
                except TypeError:
                    return inst.prepare(d)
        # 2) modül prepare
        if inspect.ismodule(strat_obj) and hasattr(strat_obj, "prepare") and callable(getattr(strat_obj, "prepare")):
            fn = getattr(strat_obj, "prepare")
            try:
                return fn(d, **_filter_kwargs_for_callable(fn, p))
            except TypeError:
                try:
                    return fn(d, p)
                except TypeError:
                    return fn(d)
        # 3) registry’den gelen prep_fn
        if callable(prep_fn):
            try:
                return prep_fn(d, **_filter_kwargs_for_callable(prep_fn, p))
            except TypeError:
                try:
                    return prep_fn(d, p)
                except TypeError:
                    return prep_fn(d)
        return d

    def _gen_bridge(d, p=None, **kw):
        """
        run_walkforward, wrapper.generate_signals(train_df, params) çağırıyor.
        Akış: instance yoksa oluştur -> PREPARE -> (ML ise tek sefer FIT) -> GENERATE
        """
        nonlocal _state
        p = {str(k): v for k, v in (p or {}).items() if k is not False}

        # 1) Instance hazırla (yoksa oluştur)
        if _state["inst"] is None:
            _state["inst"] = _make_instance(p)
        inst = _state["inst"]

        # 2) PREPARE (her çağrıda)
        d2 = _prepare_bridge(d, p)

        # 3) ML ise FİT (yalnızca bir kez)
        if hasattr(inst, "fit") and not getattr(inst, "is_trained", False) and not _state["trained"]:
            try:
                inst.fit(d2, **_filter_kwargs_for_callable(inst.fit, p))
            except TypeError:
                inst.fit(d2)
            _state["trained"] = True

        # --- ortak post-işleme: hizalama + ML için “boş sinyal kurtarma” ---
        def _post(sigseries):
            sigseries = _align_signal(sigseries, d2)
            try:
                if sigseries.abs().sum() == 0 and hasattr(inst, "predict_proba"):
                    proba = inst.predict_proba(d2)
                    if hasattr(proba, "__len__") and len(proba) > 0:
                        q_hi = float(np.nanpercentile(proba, 70))
                        q_lo = float(np.nanpercentile(proba, 30))
                        arr = np.where(proba >= q_hi, 1.0, np.where(proba <= q_lo, -1.0, 0.0))
                        sigseries = _align_signal(pd.Series(arr, index=d2.index, name="signal"), d2)
            except Exception:
                pass
            return sigseries

        # 4) GENERATE
        # 4a) instance.generate_signals
        if hasattr(inst, "generate_signals") and callable(inst.generate_signals):
            gen = inst.generate_signals
            gen_kw = _filter_kwargs_for_callable(gen, p)
            try:
                sgen = inspect.signature(gen)
                if "threshold" in sgen.parameters:
                    gen_kw.setdefault("threshold", p.get("threshold", 0.5))
                if "neutral_band" in sgen.parameters:
                    gen_kw.setdefault("neutral_band", p.get("neutral_band", 0.1))
            except Exception:
                pass
            try:
                sigres = gen(d2, **(gen_kw | kw))
            except TypeError:
                sigres = gen(d2, p, **kw)
            return _post(sigres)

        # 4b) modül fonksiyonu (RB)
        if inspect.ismodule(strat_obj) and hasattr(strat_obj, "generate_signals"):
            gen = getattr(strat_obj, "generate_signals")
            gen_kw = _filter_kwargs_for_callable(gen, p)
            try:
                sigres = gen(d2, **(gen_kw | kw))
            except TypeError:
                sigres = gen(d2, p, **kw)
            return _post(sigres)

        # 4c) registry’den çıplak gen_fn
        if callable(gen_fn):
            gen_kw = _filter_kwargs_for_callable(gen_fn, p)
            try:
                sigres = gen_fn(d2, **(gen_kw | kw))
            except TypeError:
                sigres = gen_fn(d2, p, **kw)
            return _post(sigres)

        raise RuntimeError("generate_signals bulunamadı.")

    # run_walkforward 'strategy_cls.generate_signals(df, params)' diye çağıracak
    wrapper = type("_StrategyWrapper", (object,), {
        "_param_schema": schema_wf,
        "param_schema": staticmethod(lambda: schema_wf),
        "prepare": staticmethod(_prepare_bridge),
        "generate_signals": staticmethod(_gen_bridge),
    })

    params_clean = {str(k): v for k, v in (params or {}).items() if isinstance(k, str) and k is not False}

    pool = {
        "df": df,
        "data": df,
        "schema": schema_wf,
        "params": params_clean,
        "wrapper": wrapper,
        "cls": wrapper,
        "strategy": wrapper,
        "strategy_cls": wrapper,
        "n_splits": int(n_splits),
        "commission": float(commission),
        "slippage": float(slippage),
        "capital": float(capital),
        "backtest_fn": backtest_fn,
    }
    kwargs = {k: v for k, v in pool.items() if k in names and v is not None}

    try:
        return run_walkforward_func(**kwargs)
    except TypeError:
        # df positional olabilir
        ps = list(sig.parameters.values())
        if ps and ps[0].kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            first = ps[0].name
            if first in kwargs:
                df_arg = kwargs.pop(first)
                return run_walkforward_func(df_arg, **kwargs)
        raise


# ---------- dataframe güvenli gösterim ----------
def _show_df(df, key=None):
    try:
        return st.dataframe(df, width="stretch", key=key)
    except TypeError:
        return st.dataframe(df, use_container_width=True, key=key)


# ---------- ana UI ----------
def run(state: dict):
    st.header("🚶 Walk-Forward", anchor=False)

    if "data" not in state or not isinstance(state["data"], pd.DataFrame) or state["data"].empty:
        st.warning("Önce Data sekmesinden bir veri yükleyin.")
        return

    df: pd.DataFrame = state["data"]
    if "Symbol" in df.columns:
        symbols = sorted(df["Symbol"].dropna().unique().tolist())
        sel_sym = st.selectbox("Symbol", symbols, key="wf_symbol")
        df_sym = df[df["Symbol"] == sel_sym].copy()
    else:
        sel_sym = "DATA"
        df_sym = df.copy()

    REG, ORDER = get_registry()
    keys = [k for k, _ in ORDER]
    labels = {k: n for k, n in ORDER}
    if not keys:
        st.info("Registry boş. PYTHONPATH=./src ve strateji modüllerinin import edildiğini kontrol edin.")
        return

    strat_key = st.selectbox("Strategy", keys, format_func=lambda k: labels.get(k, k), key="wf_strat")
    entry = REG[strat_key]
    schema_raw = entry.get("schema")  # list/callable/dict olabilir

    # Parametre formu
    st.subheader("Parameters")
    form_schema = schema_raw() if callable(schema_raw) else schema_raw
    raw_params = _render_param_form(form_schema or [], key_prefix=f"wf_param_{strat_key}_")
    params = _coerce_params(form_schema or [], raw_params)

    # WF ayarları
    st.subheader("Walk-Forward Settings")
    col1, col2, col3 = st.columns(3)
    with col1:
        n_splits = st.number_input("Folds", min_value=3, max_value=15, value=5, step=1, key="wf_folds")
        min_train = st.number_input("Min train bars", min_value=20, max_value=5000, value=50, step=5, key="wf_min_train")
    with col2:
        embargo = st.number_input("Embargo bars", min_value=0, max_value=1000, value=0, step=1, key="wf_embargo")
        commission_bps = st.number_input(
            "Commission (bps)", min_value=0.0, max_value=200.0, value=float(state.get("commission_bps", 5.0)),
            step=1.0, key="wf_comm_bps"
        )
    with col3:
        slippage_bps = st.number_input(
            "Slippage (bps)", min_value=0.0, max_value=300.0, value=float(state.get("slippage_bps", 10.0)),
            step=1.0, key="wf_slip_bps"
        )
        capital = st.number_input(
            "Initial capital", min_value=1000.0, max_value=1e9, value=float(state.get("capital", 100_000.0)),
            step=1000.0, key="wf_capital"
        )

    commission = commission_bps / 10_000.0
    slippage = slippage_bps / 10_000.0

    # --- Çalıştırma bütçesi kontrolleri ---
    st.subheader("Run Budget")
    colb1, colb2, colb3 = st.columns(3)
    with colb1:
        timeout_sec = st.number_input("Time budget (sec)", min_value=30, max_value=3600,
                                      value=int(state.get("wf_timeout_sec", 180)), step=30, key="wf_timeout_sec")
    with colb2:
        max_total_grid = st.number_input("Max grid size", min_value=24, max_value=2000,
                                         value=int(state.get("wf_max_grid", 96)), step=12, key="wf_max_grid")
    with colb3:
        quick_mode = st.toggle("Quick mode (coarse grid)", value=True, key="wf_quick_mode")

    # ÇALIŞTIR
    if st.button("Run Walk-Forward", key="wf_btn"):
        try:
            strat_obj_raw = entry.get("class") or entry.get("cls") or get_strategy(strat_key)
            strat_obj = strat_obj_raw or get_strategy(strat_key)

            prep_fn, gen_fn = (
                (entry.get("prep"), entry.get("gen"))
                if (entry.get("prep") or entry.get("gen"))
                else _resolve_io(strat_obj)
            )
            if gen_fn is None and not hasattr(strat_obj, "generate_signals"):
                raise RuntimeError(f"'{strat_key}' için generate_signals bulunamadı.")

            bt_fn = getattr(sdk, "run_backtest_with_signals", None)

            # --- grid önizleme ve küçültme ---
            schema_wf_preview = _to_wf_schema(form_schema)
            total_grid = _estimate_total_grid(schema_wf_preview)

            if total_grid > max_total_grid:
                shrunk = _shrink_grid(schema_wf_preview, int(max_total_grid))
                shrunk_total = _estimate_total_grid(shrunk)
                st.info(
                    f"Parametre grid’i büyük bulundu (~{total_grid}). "
                    f"Otomatik olarak ~{shrunk_total} kombinasyona küçültüldü."
                )
                schema_override = shrunk
            else:
                schema_override = schema_wf_preview

            # --- arka planda çalıştırma ---
            q = queue.Queue()

            def _target():
                try:
                    res = _wf_call_dynamic(
                        run_walkforward,
                        df_sym,
                        schema=form_schema,
                        params=dict(params),
                        prep_fn=prep_fn or (lambda d, **_: d),
                        gen_fn=gen_fn,
                        strat_obj=strat_obj,
                        n_splits=int(n_splits),
                        min_train=int(min_train),
                        embargo=int(embargo),
                        commission=float(commission),
                        slippage=float(slippage),
                        capital=float(capital),
                        backtest_fn=bt_fn,
                        schema_wf_override=schema_override,
                    )
                    q.put(("ok", res))
                except Exception as e:
                    q.put(("err", e, traceback.format_exc()))

            th = threading.Thread(target=_target, daemon=True)
            th.start()

            est = _estimate_total_grid(schema_override)
            status = st.status(f"Walk-Forward çalışıyor… (~{est} kombinasyon)", state="running")
            prog = st.progress(0)

            t0 = time.time()
            last_pct = 0
            timed_out = False
            # Monotonik sahte ilerleme: 0→97% log artış, geri sarmıyor
            while th.is_alive():
                elapsed = time.time() - t0
                pct = 97 - int(97 * math.exp(-elapsed / 3.0))
                if pct > last_pct:
                    prog.progress(pct)
                    last_pct = pct

                if elapsed > float(timeout_sec):
                    timed_out = True
                    break

                time.sleep(0.1)

            th.join(timeout=0.1)

            if timed_out:
                status.update(label=f"Zaman aşımı: işlem {int(timeout_sec)} sn’yi geçti. "
                                    f"Lütfen grid’i veya fold sayısını küçültün.", state="error")
                return

            prog.progress(100)
            status.update(label="Sonuçlar hazırlanıyor…", state="complete")

            try:
                kind, *payload = q.get(timeout=2.0)
            except Exception:
                st.error("Arka plan görevinden sonuç alınamadı.")
                return

            if kind == "ok":
                out_df = payload[0]
                _show_df(out_df, key="wf_tbl")
                st.success("Tamamlandı")
                try:
                    if isinstance(out_df, pd.DataFrame) and "Trades" in out_df.columns and (out_df["Trades"] == 0).all():
                        st.warning("Hiç trade oluşmadı. Parametre aralığını genişletin veya veri aralığını büyütün.")
                except Exception:
                    pass
            else:
                err, tb = payload[0], payload[1]
                st.error(f"Hata: {err}")
                st.code(tb)

        except Exception as e:
            st.error(f"Walk-Forward çalıştırılırken hata oluştu: {str(e)}")
            st.code(traceback.format_exc())
            show_error(e)
