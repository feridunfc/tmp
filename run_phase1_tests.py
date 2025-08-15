
import subprocess, sys

def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: {f}")
    print(r.stdout.strip())

tests = [
    "tests/test_normalizer.py",
    "tests/test_storage.py",
    "tests/test_replayer.py",
    "tests/test_indicators.py",
    "tests/test_quality.py",
]

for t in tests:
    run(t)

print("ALL_PHASE1_OK")
