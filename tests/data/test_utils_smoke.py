import importlib


def test_utils_importable():
    m = importlib.import_module("algo5.data._utils")
    assert m is not None
