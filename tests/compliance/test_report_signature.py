from pathlib import Path
import pandas as pd
from algo5.compliance.report import build_html_report
from algo5.compliance.signature import file_sha256, hmac_sha256
def test_build_and_sign(tmp_path):
    trades = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=3, freq="D"),"side":["buy","sell","buy"],"qty":[1,1,1],"price":[100,101,102]})
    metrics = {"sharpe": 1.0, "trades": 3}
    path = build_html_report("t01", metrics, trades, outdir=tmp_path)
    assert Path(path).exists()
    sha = file_sha256(path); assert len(sha) == 64
    sig = hmac_sha256(path, "secret"); assert len(sig) == 64; assert sha != sig
