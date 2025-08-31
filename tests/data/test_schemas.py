
import pandas as pd
from src.algo5.data.schemas import OhlcvSchema

def test_canonicalize_and_coerce_dtypes():
    df = pd.DataFrame(
        {"open":[1,2], "high":[1,2], "low":[1,2], "close":[1,2], "Volume":[1,2]}
    )
    sch = OhlcvSchema()
    df2, rep = sch.coerce_dtypes(df)
    assert set(sch.required).issubset(df2.columns)
    ok, mism = sch.validate_dtypes(df2)
    assert ok, mism

def test_json_schema_exports():
    sch = OhlcvSchema()
    try:
        rec = sch.json_record_schema()
        pay = sch.json_payload_schema()
        assert rec and pay
    except RuntimeError:
        # pydantic not installed: acceptable for environments without JSON schema export
        pass
