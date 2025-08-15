
import subprocess, sys
def run(f):
    r = subprocess.run([sys.executable, f], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise SystemExit(f"FAILED: %s" % f)
    print(r.stdout.strip())
tests = ["/mnt/data/tests/test_rate_limit_and_live_stub.py"]
for t in tests:
    run(t)
print("ALL_PHASE9_OK")
