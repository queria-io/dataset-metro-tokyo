"""ABR のスナップショットを作って戻せること。

CI は ABR の配布元に届かないので、スナップショットの展開が取得の代わりになる。
展開に失敗したときは、配布元からの取得に切り替わること。
"""

from unittest.mock import patch

from pipelines import geocode


def make_abrg_dir(root):
    abrg = root / "abrg"
    (abrg / "database").mkdir(parents=True)
    (abrg / "database" / "common.sqlite").write_bytes(b"SQLite format 3\x00")
    (abrg / "cache").mkdir()
    (abrg / "cache" / "trie.bin").write_bytes(b"\x01\x02")
    (abrg / "download").mkdir()
    (abrg / "download" / "leftover.zip").write_bytes(b"PK\x03\x04")
    return abrg


def test_snapshot_round_trip_keeps_database_and_cache_only(tmp_path):
    archive = tmp_path / "snapshot.tar.gz"
    geocode.make_snapshot(make_abrg_dir(tmp_path), archive)

    restored = tmp_path / "restored"
    assert geocode.restore_snapshot(restored, url=archive.as_uri())

    assert (restored / "database" / "common.sqlite").read_bytes() == b"SQLite format 3\x00"
    assert (restored / "cache" / "trie.bin").read_bytes() == b"\x01\x02"
    assert not (restored / "download").exists()


def test_missing_snapshot_returns_false(tmp_path):
    assert not geocode.restore_snapshot(tmp_path / "abrg", url=(tmp_path / "none.tar.gz").as_uri())


def write_ods(tmp_path):
    ods = tmp_path / "ods"
    ods.mkdir()
    (ods / "aed.ndjson").write_text(
        '{"address": "東京都清瀬市中里五丁目842", "_org_code": "t132217", "_org_title": "清瀬市"}\n',
        encoding="utf-8",
    )
    return ods


def run_geocode(tmp_path, restored):
    with (
        patch.object(geocode, "_node_major", return_value=22),
        patch.object(geocode, "restore_snapshot", return_value=restored) as restore,
        patch.object(geocode, "download_abr") as download,
        patch.object(geocode, "run_geocoder"),
        patch.object(geocode, "_load_results", return_value={}),
    ):
        geocode.geocode(str(write_ods(tmp_path)), str(tmp_path / "geocode"), extra_files=[])
    return restore, download


def test_snapshot_replaces_download(tmp_path):
    restore, download = run_geocode(tmp_path, restored=True)

    restore.assert_called_once()
    download.assert_not_called()


def test_download_is_used_when_snapshot_is_unavailable(tmp_path):
    _, download = run_geocode(tmp_path, restored=False)

    download.assert_called_once()
