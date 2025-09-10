# src/strategies/registry.py
from __future__ import annotations

import importlib
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger(__name__)

# =============================================================================
# Public API
# =============================================================================
__all__ = [
    "register_strategy", "register_ml", "register_rule", "register_hybrid",
    "list_strategies", "create", "get_registry", "get_strategy",
    "discover_strategies", "get_strategy_class", "get_param_schema",
    "bootstrap", "Field", "StrategyParameters",
]

# =============================================================================
# Base sınıfları güvenli import (AI + Rule-based)
# =============================================================================
try:
    from strategies.base_strategy import BaseStrategy as AILearningBase
    try:
        from strategies.base_strategy import StrategyParameters as _StrategyParameters
    except Exception:
        _StrategyParameters = Any
except Exception:
    class AILearningBase:  # type: ignore[no-redef]
        """Fallback: AI base bulunamadı (discovery yine çalışır)."""
        pass
    _StrategyParameters = Any  # type: ignore[misc,assignment]

try:
    from strategies.base import Strategy as RuleBasedBase
except Exception:
    class RuleBasedBase:  # type: ignore[no-redef]
        """Fallback: Rule-based base bulunamadı (discovery yine çalışır)."""
        pass

StrategyParameters = _StrategyParameters  # dışa açık tip alias

# =============================================================================
# Parametre alanı (UI/HPO için)
# =============================================================================
@dataclass(frozen=True)
class Field:
    name: str
    type: Any
    default: Any = None
    low: Optional[float] = None
    high: Optional[float] = None
    options: Optional[List[Any]] = None
    step: Optional[float] = None
    help: Optional[str] = None

# =============================================================================
# Kayıt defteri (dict tabanlı spec tutar)
# =============================================================================
# STRATEGY_REGISTRY[key] = {
#   "name": str, "display_name": str, "family": str,
#   "prep": callable|None, "gen": callable, "schema": list[Field]|list[dict],
#   "cls": Type|None, "module": str
# }
STRATEGY_REGISTRY: Dict[str, Dict[str, Any]] = {}

def register_strategy(name: str):
    """Sınıf/Factory fonksiyonlarını registry'e eklemek için dekoratör."""
    def deco(cls_or_fn):
        _try_register(name, cls_or_fn)
        return cls_or_fn
    return deco

# Eski alias’lar
def register_ml(name: str):     return register_strategy(name)
def register_rule(name: str):   return register_strategy(name)
def register_hybrid(name: str): return register_strategy(name)

def list_strategies() -> List[str]:
    return sorted(STRATEGY_REGISTRY.keys())

def create(name: str, *args, **kwargs):
    """Registry anahtarıyla instance oluşturmak istersen (factory ile)."""
    spec = STRATEGY_REGISTRY.get(name)
    if not spec:
        raise KeyError(f"Strategy '{name}' not found. Available: {list_strategies()}")
    cls = spec.get("cls")
    if inspect.isclass(cls):
        return cls(*args, **kwargs)
    factory = spec.get("factory")
    if callable(factory):
        return factory(*args, **kwargs)
    raise TypeError(f"Strategy '{name}' is not instantiable (no class/factory).")

def get_registry() -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Eski UI/araçlar uyumu:
      REG   -> dict  (key -> spec dict)
      ORDER -> [(key, display_name), ...] family + display_name sıralı
    """
    # sıralı görünüm
    items = sorted(
        STRATEGY_REGISTRY.items(),
        key=lambda kv: (
            kv[1].get("family", "zzz"),
            kv[1].get("display_name") or kv[1].get("name") or kv[0]
        ),
    )
    order = [(k, v.get("display_name") or v.get("name") or k) for k, v in items]
    return STRATEGY_REGISTRY, order

# =============================================================================
# Esnek import yardımcıları
# =============================================================================
def _import_module_lenient(modpath: str):
    """
    'strategies.xxx' ve 'src.strategies.xxx' arasında otomatik geçiş.
    PYTHONPATH=./src olmasa bile toleranslı çalışır.
    """
    try:
        return importlib.import_module(modpath)
    except ModuleNotFoundError:
        if modpath.startswith("src."):
            alt = modpath[len("src."):]
        else:
            alt = "src." + modpath
        return importlib.import_module(alt)

def _import_from_path(spec: str) -> Optional[type]:
    """'pkg.mod:ClassName' -> Class obj (yoksa None)."""
    modpath, _, clsname = spec.partition(":")
    if not modpath or not clsname:
        return None
    try:
        module = _import_module_lenient(modpath)
        return getattr(module, clsname, None)
    except Exception as e:
        logger.info("static bind skipped: %s (%s)", spec, e)
        return None

# =============================================================================
# Adaptör: sınıfı/modülü tek tip sözlüğe çevir
# =============================================================================
def _guess_family(module_name: str, default: str = "conventional") -> str:
    if ".ai." in module_name:
        return "ai"
    if ".ml_" in module_name or ".ml." in module_name:
        return "ai"
    if ".rule_based." in module_name or ".rules." in module_name:
        return "rule_based"
    if ".hybrid." in module_name:
        return "hybrid"
    return default

def _resolve_callable(obj: Any, name: str) -> Optional[Callable[..., Any]]:
    fn = getattr(obj, name, None)
    if fn is None:
        return None
    # staticmethod/classmethod/normal function -> underlying function
    if isinstance(fn, (staticmethod, classmethod)):
        return fn.__func__  # type: ignore[attr-defined]
    if callable(fn):
        return fn
    return None

def _adapt_to_spec(obj: Any) -> Dict[str, Any]:
    """
    Sınıf ya da modül benzeri objeyi bir spec sözlüğüne dönüştür.
    Zorunlular: gen (generate_signals)
    Opsiyoneller: prep (prepare), schema (list[Field]|list[dict])
    """
    mod = getattr(obj, "__module__", "") or getattr(obj, "__name__", "") or ""
    display_name = getattr(obj, "name", None) or getattr(obj, "__name__", None) or "Strategy"
    family = getattr(obj, "family", None) or _guess_family(mod)

    # Fonksiyonları çöz
    prep = _resolve_callable(obj, "prepare")
    gen = _resolve_callable(obj, "generate_signals")
    ps  = _resolve_callable(obj, "param_schema")

    # Eğer sınıf değil de modül düzeyi fonksiyonlar varsa (param_schema/prepare/generate_signals)
    if gen is None and hasattr(obj, "__dict__"):
        gen = obj.__dict__.get("generate_signals") if callable(obj.__dict__.get("generate_signals")) else None
    if prep is None and hasattr(obj, "__dict__"):
        prep = obj.__dict__.get("prepare") if callable(obj.__dict__.get("prepare")) else None
    if ps is None and hasattr(obj, "__dict__"):
        ps = obj.__dict__.get("param_schema") if callable(obj.__dict__.get("param_schema")) else None

    if gen is None:
        raise TypeError(f"generate_signals missing on {obj}")

    # Şemayı hazır listeye çevir (UI, HPO tüketir)
    schema: List[Any] = []
    try:
        raw = ps() if callable(ps) else None
        if isinstance(raw, list):
            schema = raw
    except Exception as e:
        logger.info("param_schema() failed on %s: %s", obj, e)

    return {
        "name": display_name,
        "display_name": display_name,
        "family": family,
        "prep": prep,     # None olabilir
        "gen": gen,       # zorunlu
        "schema": schema, # liste (Field/dict)
        "cls": obj if inspect.isclass(obj) else None,
        "module": mod,
    }

def _try_register(key: str, cls_or_obj: Any) -> bool:
    try:
        spec = _adapt_to_spec(cls_or_obj)
    except Exception as e:
        logger.warning("register skipped: %s (%s)", key, e)
        return False
    STRATEGY_REGISTRY[key] = spec
    logger.debug("strategy registered: %s (%s)", key, spec.get("display_name"))
    return True

# =============================================================================
# Statik bağlar (lazy import) – mevcut olmayanlar sessizce atlanır
# =============================================================================
_STATIC_BINDINGS: List[Tuple[str, str]] = [
    # --- Rule-based ---
    ("rb_ma_crossover",  "strategies.rule_based.ma_crossover:MACrossover"),
    ("rb_atr_breakout",  "strategies.rule_based.atr_breakout:ATRBreakout"),

    # --- ML (varsa; yoksa sessizce atlanır) ---
    ("ai_random_forest", "strategies.ml_models.random_forest_strategy:RandomForestStrategy"),
]

def _bootstrap_static_bindings() -> int:
    added = 0
    for key, spec in _STATIC_BINDINGS:
        if key in STRATEGY_REGISTRY:
            continue
        cls = _import_from_path(spec)
        if cls is None:
            continue
        if _try_register(key, cls):
            added += 1
    if added:
        logger.info("static bindings registered +%d (total=%d)", added, len(STRATEGY_REGISTRY))
    return added

# =============================================================================
# Auto-discovery (opsiyonel)
# =============================================================================
@dataclass(frozen=True)
class StrategySpec:
    qualified_name: str
    display_name: str
    family: str
    module: str
    cls: Type
    param_schema: Optional[Type[Any]]

def _looks_like_strategy_class(obj: Any) -> bool:
    if not inspect.isclass(obj) or inspect.isabstract(obj):
        return False
    if getattr(obj, "is_strategy", False):
        return True
    try:
        if issubclass(obj, (AILearningBase, RuleBasedBase)):
            return True
    except Exception:
        pass
    has_train = callable(getattr(obj, "fit", None)) or callable(getattr(obj, "train", None))
    has_pred  = callable(getattr(obj, "predict", None)) or callable(getattr(obj, "predict_proba", None))
    return has_train and has_pred

def discover_strategies() -> Dict[str, StrategySpec]:
    # Hem 'strategies' hem 'src.strategies' dene
    try:
        root = _import_module_lenient("strategies")
    except Exception:
        root = _import_module_lenient("src.strategies")

    results: Dict[str, StrategySpec] = {}
    errors: Dict[str, str] = {}
    skip_contains = (
        ".features", ".strategy_factory", ".registry", ".adapters", ".base",
        ".hybrid_v1", ".ai.logreg_strategy", ".ai.rf_strategy"
    )

    candidates: List[str] = []
    if hasattr(root, "__path__"):
        import pkgutil
        for mi in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
            name = mi.name
            if any(s in name for s in skip_contains):
                continue
            candidates.append(name)

    if not candidates:
        for pkg in (
            "strategies.rule_based", "strategies.ai", "strategies.hybrid",
            "src.strategies.rule_based", "src.strategies.ai", "src.strategies.hybrid",
        ):
            try:
                mod = _import_module_lenient(pkg)
                if hasattr(mod, "__path__"):
                    import pkgutil
                    for mi in pkgutil.walk_packages(mod.__path__, mod.__name__ + "."):
                        name = mi.name
                        if any(s in name for s in skip_contains):
                            continue
                        candidates.append(name)
            except Exception as e:
                errors[pkg] = f"{type(e).__name__}: {e}"

    for name in candidates:
        try:
            m = _import_module_lenient(name)
            for _, obj in inspect.getmembers(m, _looks_like_strategy_class):
                qn = f"{obj.__module__}.{obj.__name__}"
                family = getattr(obj, "family", None) or _guess_family(obj.__module__)
                spec = StrategySpec(
                    qualified_name=qn,
                    display_name=getattr(obj, "name", getattr(obj, "display_name", obj.__name__)),
                    family=family,
                    module=obj.__module__,
                    cls=obj,
                    param_schema=getattr(obj, "ParamSchema", None),
                )
                results[qn] = spec
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}"

    discover_strategies.errors = errors  # UI’de görmek isteyenler için
    return results

# =============================================================================
# get_strategy / helpers
# =============================================================================
class _StrategyWrapper:
    """
    UI ve testler için tek tip arayüz:
      .prepare(df, **params) -> pd.DataFrame (opsiyonel; yoksa df döner)
      .generate_signals(df, **params) -> pd.Series
      .param_schema() -> list[Field|dict]
      .name / .family
    """
    def __init__(self, spec: Dict[str, Any]):
        self._spec = spec
        self.name = spec.get("display_name") or spec.get("name")
        self.family = spec.get("family")

    def prepare(self, df, **params):
        prep = self._spec.get("prep")
        return df if prep is None else prep(df, **params)

    def generate_signals(self, df, **params):
        gen = self._spec.get("gen")
        if not callable(gen):
            raise TypeError("strategy has no 'generate_signals'")
        return gen(df, **params)

    def param_schema(self):
        return self._spec.get("schema") or []

def get_strategy_class(qualified_name: str) -> Type:
    module_name, class_name = qualified_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)

def get_param_schema(qualified_name: str) -> Any:
    cls = get_strategy_class(qualified_name)
    fn = _resolve_callable(cls, "param_schema")
    if callable(fn):
        return fn()
    return []

def get_strategy(name: str):
    """
    - Registry anahtarıyla döndür (wrapper)
    - 'pkg.mod:ClassName' veya 'pkg.mod.ClassName' biçimlerini destekle
    """
    if name in STRATEGY_REGISTRY:
        return _StrategyWrapper(STRATEGY_REGISTRY[name])

    # 'module:Class'
    if ":" in name:
        cls = _import_from_path(name)
        if cls is not None:
            spec = _adapt_to_spec(cls)
            return _StrategyWrapper(spec)

    # 'module.Class'
    if "." in name:
        try:
            cls = get_strategy_class(name)
            spec = _adapt_to_spec(cls)
            return _StrategyWrapper(spec)
        except Exception:
            pass

    raise KeyError(f"Strategy '{name}' not found. Available keys: {list_strategies()}")

# =============================================================================
# Bootstrap
# =============================================================================
def _bootstrap_autodiscovery() -> int:
    """
    strategies.plugins.auto_register.bootstrap() mevcutsa çağırır.
    Yoksa sessizce 0 döner.
    """
    try:
        from strategies.plugins.auto_register import bootstrap as _auto
    except Exception as e:
        logger.debug("auto_register not available: %s", e)
        return 0
    before = len(STRATEGY_REGISTRY)
    gained = _auto()  # dış fonksiyon dict doldurabilir
    logger.info("auto_discovery registered +%d strategies (total=%d)",
                gained, len(STRATEGY_REGISTRY))
    return len(STRATEGY_REGISTRY) - before

def bootstrap(mode: str = "auto", strict: bool = False) -> int:
    """
    mode:
      - "auto": önce auto_register.bootstrap() dener; 0 eklenirse statik fallback’e geçer
      - "static": sadece statik bağlar
      - "both": önce auto, sonra statik
    strict: True ise hiç strateji kayıt edilemezse hata fırlatır.
    """
    before = len(STRATEGY_REGISTRY)
    gained = 0

    if mode in ("auto", "both"):
        gained += _bootstrap_autodiscovery()

    if mode in ("static", "both") or (mode == "auto" and gained == 0):
        gained += _bootstrap_static_bindings()

    total = len(STRATEGY_REGISTRY)
    if strict and total == 0:
        raise RuntimeError("No strategies registered. Check optional deps and paths.")
    logger.debug("bootstrap done: +%d (total=%d)", total - before, total)
    return total - before
