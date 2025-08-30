import pytest
from algo5.api.server import APIServer
from algo5.api.security import AuthError
def test_api_key_and_calls():
    srv = APIServer(api_key="k")
    with pytest.raises(AuthError): srv.strategies_list(key="wrong")
    out = srv.strategies_list(key="k"); assert "strategies" in out
    r = srv.backtest_run({"strategy":"sma"}, key="k"); assert r["status"]=="ok" and r["run_id"].startswith("run_")
    runs = srv.runs(key="k")["runs"]; assert len(runs)==1
