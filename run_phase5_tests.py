
import subprocess, sys

def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: %s" % f)
    print(r.stdout.strip())

tests = [
    "tests/test_twap_vwap_sor.py",
    "tests/test_ems_integration.py",
    "tests/test_tca_calc.py",
]

for t in tests:
    run(t)

print("ALL_PHASE5_OK")
