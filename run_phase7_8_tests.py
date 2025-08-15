
import subprocess, sys

def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: %s" % f)
    print(r.stdout.strip())

tests = [
    "tests/test_orchestrator_end_to_end.py",
    "tests/test_retraining_hyperopt.py",
]

for t in tests:
    run(t)

print("ALL_PHASE7_8_OK")
