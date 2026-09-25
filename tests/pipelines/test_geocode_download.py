"""ABR データの取得で、zip でないファイルを見つけて取り直すことを確かめる。

abrg は HTTP のステータスを見ずに応答を保存するので、取得元がエラーページを返すと
HTML が .zip の名前で download/ に残る。abrg の実行（_abrg）だけを差し替え、
download/ に実際のファイルを置いて download_abr() の判定と取り直しを見る。
取得元への問い合わせ（_probe_source）はネットワークに出るので記録だけにする。
"""

import logging
import subprocess
import zipfile

import pytest

from pipelines import geocode

HTML = b'<!DOCTYPE html>\n<html lang="ja">\n<head>\n<title>403 Forbidden</title>'


def write_zip(path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mt_town_city131016.csv", "lg_code,machiaza_id\n131016,0001001\n")


def test_find_broken_zips(tmp_path):
    write_zip(tmp_path / "good.csv.zip")
    (tmp_path / "html.csv.zip").write_bytes(HTML)
    # 書きかけの zip は先頭が PK でも中央ディレクトリが無い
    write_zip(tmp_path / "full.zip")
    (tmp_path / "truncated.csv.zip").write_bytes((tmp_path / "full.zip").read_bytes()[:20])
    (tmp_path / "full.zip").unlink()
    # 展開済みの CSV は対象外
    (tmp_path / "mt_town_city131016.csv").write_text("x")

    broken = geocode.find_broken_zips(tmp_path)

    assert [p.name for p in broken] == ["html.csv.zip", "truncated.csv.zip"]


def test_find_broken_zips_without_dir(tmp_path):
    assert geocode.find_broken_zips(tmp_path / "missing") == []


class FakeAbrg:
    """呼ばれるたびに download/ に置くファイルと、終わり方を順に返す。"""

    def __init__(self, abrg_dir, steps):
        self.download_dir = abrg_dir / "download"
        self.steps = list(steps)
        self.calls = 0

    def __call__(self, args, timeout):
        self.calls += 1
        files, error = self.steps.pop(0)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (self.download_dir / name).write_bytes(data)
        if error is not None:
            raise error


@pytest.fixture
def probed(monkeypatch):
    names: list[list[str]] = []
    monkeypatch.setattr(geocode, "_probe_source", names.append)
    return names


def test_retry_after_html_and_hang(tmp_path, monkeypatch, probed, caplog):
    # 1 回目: HTML を残して止まり、打ち切られる。2 回目: 正常に終わる
    hang = subprocess.TimeoutExpired(["abrg"], geocode.DOWNLOAD_TIMEOUT)
    fake = FakeAbrg(tmp_path, [({"mt_town_city131024.csv.zip": HTML}, hang), ({}, None)])
    monkeypatch.setattr(geocode, "_abrg", fake)

    with caplog.at_level(logging.WARNING, logger="pipelines"):
        geocode.download_abr(tmp_path, retry_waits=(0, 0))

    assert fake.calls == 2
    assert probed == [["mt_town_city131024.csv.zip"]]
    assert not (tmp_path / "download" / "mt_town_city131024.csv.zip").exists()
    assert "mt_town_city131024.csv.zip" in caplog.text
    assert "<title>403 Forbidden</title>" in caplog.text


def test_fail_when_html_persists(tmp_path, monkeypatch, probed):
    step = ({"mt_pref_all.csv.zip": HTML}, None)
    fake = FakeAbrg(tmp_path, [step, step, step])
    monkeypatch.setattr(geocode, "_abrg", fake)

    with pytest.raises(SystemExit, match="mt_pref_all.csv.zip"):
        geocode.download_abr(tmp_path, retry_waits=(0, 0))

    assert fake.calls == 3


def test_fail_fast_on_hang_without_broken_zip(tmp_path, monkeypatch, probed):
    hang = subprocess.TimeoutExpired(["abrg"], geocode.DOWNLOAD_TIMEOUT)
    fake = FakeAbrg(tmp_path, [({}, hang)])
    monkeypatch.setattr(geocode, "_abrg", fake)

    with pytest.raises(SystemExit, match="timed out"):
        geocode.download_abr(tmp_path, retry_waits=(0, 0))

    assert fake.calls == 1
    assert probed == []


def test_success_without_broken_zip(tmp_path, monkeypatch, probed):
    fake = FakeAbrg(tmp_path, [({}, None)])
    monkeypatch.setattr(geocode, "_abrg", fake)

    geocode.download_abr(tmp_path, retry_waits=(0, 0))

    assert fake.calls == 1
    assert probed == []


class _ResetWhileReading:
    """ヘッダーまでは返すが、本文の読み取りで接続が切れる応答。"""

    status = 200
    headers = {"Content-Type": "text/html"}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, _size):
        raise ConnectionResetError("reset while reading")


def test_probe_url_swallows_read_errors(monkeypatch, caplog):
    # 取得元の応答が不安定なときに呼ばれるので、読み取りの失敗で取り直しを止めない
    monkeypatch.setattr(geocode, "urlopen", lambda *a, **k: _ResetWhileReading())
    with caplog.at_level(logging.WARNING, logger="pipelines"):
        geocode._probe_url("https://example.invalid/mt_town_city131016.csv.zip")
    assert "reset while reading" in caplog.text
