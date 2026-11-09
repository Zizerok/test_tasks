import os
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    result = subprocess.run([sys.executable, "scripts/prepare_test_db.py"], check=False)
    if result.returncode:
        return result.returncode
    (root / "reports").mkdir(exist_ok=True)
    os.execv(
        sys.executable,
        [
            sys.executable,
            "-m",
            "pytest",
            "backend_tests",
            "-v",
            "--junitxml=reports/pytest.xml",
            *sys.argv[1:],
        ],
    )


if __name__ == "__main__":
    sys.exit(main())
