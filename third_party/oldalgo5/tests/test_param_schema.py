import pytest
from src.core.strategies._schema import get_registry, validate_params
import importlib
def test_registry_and_schema():
    import src.core.strategies.ma_crossover  # ensure registration
    reg = get_registry()
    assert "MACrossover" in reg
    sch = reg["MACrossover"]["schema"]
    assert "short_window" in sch and "long_window" in sch
def test_validation_edge_cases():
    import src.core.strategies.ma_crossover  # ensure registration
    reg = get_registry(); sch = reg["MACrossover"]["schema"]
    with pytest.raises(Exception):
        validate_params(sch, {"short_window":1,"long_window":500})
