# precommit_pytest.py
"""
Pre-commit pytest runner
- Çalışma ağacına dosya bırakmaz (coverage dosyaları tmp'e gider)
- pytest.ini içindeki addopts'i etkisizleştirir (XML/HTML rapor vs.)
"""
import os
import shutil
import subprocess
import tempfile


def main() -> int:
    tmpdir = tempfile.mkdtemp(prefix="pcov_")
    try:
        env = os.environ.copy()
        # Coverage verisi geçici dizine
        env["COVERAGE_FILE"] = os.path.join(tmpdir, ".coverage")

        cmd = [
            "pytest",
            "-q",
            "--override-ini=addopts=",  # pytest.ini'deki addopts'i sıfırla
            "--cov=src/algo5",
            "--cov-report=term-missing",  # sadece terminal raporu
            "--cov-report=",  # XML/HTML yok
        ]
        return subprocess.call(cmd, env=env)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
