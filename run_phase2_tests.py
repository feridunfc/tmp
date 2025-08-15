
import subprocess, sys

def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: {f}")
    print(r.stdout.strip())

tests = [
    "tests/test_signal_rules.py",
    "tests/test_pipeline_basic.py",
]

for t in tests:
    run(t)

print("ALL_PHASE2_OK")
