
import subprocess, sys

def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: %s" % f)
    print(r.stdout.strip())

tests = [
    "tests/test_metrics_calc.py",
    "tests/test_backtest_walkforward.py",
]

for t in tests:
    run(t)

print("ALL_PHASE3_OK")
