"""ABR のスナップショットを作り直して assets.queria.io に置く。

ABR の配布元は国外からの取得に 403 を返すので、**日本から実行する。**
CI はここで置いたスナップショットを展開して、配布元からの取得の代わりにする
（pipelines/geocode.py の ABR_SNAPSHOT_URL）。

    mise exec node@22.22.0 -- uv run python scripts/refresh_abr_snapshot.py            # 作るだけ
    mise exec node@22.22.0 -- uv run python scripts/refresh_abr_snapshot.py --upload   # 作って置く

置いたあと pipelines/geocode.py の ABR_SNAPSHOT_DATE を出力された日付に書き換えて PR にする。
同じ名前で上書きすると CDN が古い中身を返し続けるので、名前には作った日付を入れる。
アップロードは Cloudflare の公式 CLI（cf）で行う。1 オブジェクト 300MB まで。
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipelines.geocode import ABRG_VERSION, download_abr, make_snapshot  # noqa: E402

BUCKET = "queria-assets"
#: FLOPS のアカウント。cf はアカウントを2つ持つ環境で非対話だと止まるので明示する
CLOUDFLARE_ACCOUNT_ID = "57c6a116efc637fc3f21d0affea15508"
#: cf r2 objects put の上限
MAX_UPLOAD_BYTES = 300 * 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upload", action="store_true", help="assets.queria.io に置く")
    parser.add_argument("--out", default="data/abr-snapshot.tar.gz", help="書き出し先")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    stamp = date.today().strftime("%Y%m%d")
    key = f"abr/abrg-{ABRG_VERSION}-tokyo-{stamp}.tar.gz"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        abrg_dir = Path(tmp) / "abrg"
        download_abr(abrg_dir)
        make_snapshot(abrg_dir, out)

    size = out.stat().st_size
    print(f"{out}: {size / 1024 / 1024:.1f} MB")
    if not args.upload:
        print(f"置くときは --upload を付ける（{key}）")
        return
    if size > MAX_UPLOAD_BYTES:
        sys.exit(f"{size} バイトあり、cf で置ける上限（300MB）を超える")

    subprocess.run(
        [
            "cf", "r2", "objects", "put", key,
            "--bucket-name", BUCKET,
            "--file", str(out),
            "--content-type", "application/gzip",
        ],
        check=True,
        env={**os.environ, "CLOUDFLARE_ACCOUNT_ID": CLOUDFLARE_ACCOUNT_ID},
    )
    print(f"置いた: https://assets.queria.io/{key}")
    print(f'pipelines/geocode.py の ABR_SNAPSHOT_DATE を "{stamp}" にする')


if __name__ == "__main__":
    main()
