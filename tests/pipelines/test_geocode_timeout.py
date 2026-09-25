"""abrg の打ち切りが、孫プロセスまで止めてから例外を投げることを確かめる。

abrg は npx → sh → node と子を重ねて動く。打ち切りで npx だけを止めると node が
残り、次の取り直しと同じ sqlite を奪い合う。ここでは sh の下に sleep を置いて
同じ親子関係を作り、実際にプロセスを起動して確かめる（モックしない）。
"""

import os
import subprocess
import time

import pytest

from pipelines.geocode import run_with_timeout


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def test_timeout_kills_grandchild(tmp_path):
    pid_file = tmp_path / "grandchild.pid"
    # sh が sleep を子として起動し、その pid を書いてから待つ
    cmd = ["sh", "-c", f"sleep 60 & echo $! > {pid_file}; wait"]

    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        run_with_timeout(cmd, timeout=1)
    assert time.monotonic() - started < 15

    grandchild = int(pid_file.read_text())
    # SIGKILL 後の回収は非同期なので少しだけ待つ
    for _ in range(50):
        if not _alive(grandchild):
            break
        time.sleep(0.1)
    assert not _alive(grandchild), "打ち切り後も孫プロセスが残っている"


def test_nonzero_exit_raises():
    with pytest.raises(subprocess.CalledProcessError):
        run_with_timeout(["sh", "-c", "exit 3"], timeout=10)


def test_success_returns():
    run_with_timeout(["sh", "-c", "exit 0"], timeout=10)
