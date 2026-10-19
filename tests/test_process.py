import subprocess
import sys
from pathlib import Path


def test_malformed_stdin_utf8_is_reported_by_real_module_process() -> None:
    repository_root = Path(__file__).resolve().parent.parent

    result = subprocess.run(
        [sys.executable, "-m", "crossmill", "stats", "-"],
        input=b"AB\xff\n",
        cwd=repository_root,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr == b"crossmill: <stdin>: input is not valid UTF-8\n"
