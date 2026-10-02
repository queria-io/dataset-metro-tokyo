"""ABR のスナップショットを作り直して assets.queria.io に置く。

ABR の配布元は国外からの取得に 403 を返すので、**日本から実行する。**
CI はここで置いたスナップショットを展開して、配布元からの取得の代わりにする
（pipelines/geocode.py の ABR_SNAPSHOT_URL）。

    mise exec node@22.22.0 -- uv run python scripts/refresh_abr_snapshot.py            # 作るだけ
    mise exec node@22.22.0 -- uv run python scripts/refresh_abr_snapshot.py --upload   # 作って置く

置いたあと pipelines/geocode.py の ABR_SNAPSHOT_DATE を出力された日付に書き換えて PR にする。
同じ名前で上書きすると CDN が古い中身を返し続けるので、名前には作った日付を入れる。
アップロードは Cloudflare の公式 CLI（cf）で行う。cf はリクエストを30秒で打ち切るので、
断片に分けて置き、最後に断片の一覧（目録）を置く。目録が無ければ CI は使わない。
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipelines.geocode import (  # noqa: E402
    ABRG_VERSION,
    download_abr,
    make_snapshot,
    split_snapshot,
)

BUCKET = "queria-assets"
#: FLOPS のアカウント。cf はアカウントを2つ持つ環境で非対話だと止まるので明示する
CLOUDFLARE_ACCOUNT_ID = "57c6a116efc637fc3f21d0affea15508"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upload", action="store_true", help="assets.queria.io に置く")
    parser.add_argument("--out", default="data/abr-snapshot", help="書き出し先のディレクトリ")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    stamp = date.today().strftime("%Y%m%d")
    name = f"abrg-{ABRG_VERSION}-tokyo-{stamp}"
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{name}.tar.gz"

    with tempfile.TemporaryDirectory() as tmp:
        abrg_dir = Path(tmp) / "abrg"
        download_abr(abrg_dir)
        make_snapshot(abrg_dir, archive)

    manifest = split_snapshot(archive, out_dir / "parts")
    manifest_path = out_dir / f"{name}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{archive}: {archive.stat().st_size / 1024 / 1024:.1f} MB, 断片 {len(manifest['parts'])} 個")
    if not args.upload:
        print(f"置くときは --upload を付ける（abr/{name}.json）")
        return

    # 目録を最後に置く。途中で止まっても、目録が無ければ CI はこの版を使わない
    for part in manifest["parts"]:
        put(f"abr/{part['name']}", out_dir / "parts" / part["name"], "application/octet-stream")
    put(f"abr/{name}.json", manifest_path, "application/json")
    print(f"置いた: https://assets.queria.io/abr/{name}.json")
    print(f'pipelines/geocode.py の ABR_SNAPSHOT_DATE を "{stamp}" にする')


def put(key: str, path: Path, content_type: str) -> None:
    subprocess.run(
        [
            "cf", "r2", "objects", "put", key,
            "--bucket-name", BUCKET,
            "--file", str(path),
            "--content-type", content_type,
        ],
        check=True,
        env={**os.environ, "CLOUDFLARE_ACCOUNT_ID": CLOUDFLARE_ACCOUNT_ID},
    )


if __name__ == "__main__":
    main()
