
import subprocess, sys

def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: %s" % f)
    print(r.stdout.strip())

tests = [
    "tests/test_metrics_and_events.py",
    "tests/test_alerts_drawdown.py",
    "tests/test_reporting_builder.py",
]

for t in tests:
    run(t)

print("ALL_PHASE6_OK")
