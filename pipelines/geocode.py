"""住所を ABR（アドレス・ベース・レジストリ）でジオコーディングする。

data/ods/*.ndjson と EXTRA_ADDRESS_FILES の住所を abr-geocoder に通し、結果を
(組織コード, 住所) 単位で data/geocode/addresses.ndjson に出力する。
models/ods/raw/raw_geocode.sql がこれを読み、ods の各 stg モデルが原典の緯度経度が
無い行の補完に使う。hokenjo の台帳は緯度経度を持たないので、座標はここだけから来る。

自治体が公開した緯度経度は施設の 54% にしか無く、残りは住所しか手がかりがない。
住所は原典のまま突き合わせられるよう、正規化はこのモジュールの中だけで完結させ、
出力には原典の住所文字列をそのまま持たせる（SQL 側に正規化を持ち込まない）。
"""

import json
import logging
import os
import shutil
import signal
import subprocess
import time
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

#: 使う abr-geocoder のバージョン。上げるときは採用率を測ってから
ABRG_VERSION = "2.3.1"

#: abrg download の打ち切り（秒）。東京都62市区町村（zip 187 個）の取得は手元の実測で
#: 82〜88 秒。CI ランナーは CPU が遅く取得元（東京）から遠いので、数倍かかっても収まる値にする。
#: abrg は取得に失敗したファイルを飛ばしたあと終了せずに止まることがあり、
#: 打ち切りが無いとジョブの上限（6 時間）まで待ち続ける
DOWNLOAD_TIMEOUT = 600

#: abrg でのジオコーディングの打ち切り（秒）。手元の実測で ods の約 4.1 万件が 7 秒、
#: 保健所台帳の約 3.3 万件が 6 秒（どちらも npx の起動込み）。合わせて 10 秒台なので、
#: 住所が数倍に増えても収まる
GEOCODE_TIMEOUT = 300

#: 打ち切ったあと SIGKILL を送るまでの猶予（秒）
KILL_GRACE = 10

#: 取得した zip が壊れていたときに取り直すまでの待ち（秒）。要素の数が取り直しの回数。
#: abrg は取り込み済みのファイルを飛ばすので、取り直しで落ちてくるのは壊れていた分だけ
DOWNLOAD_RETRY_WAITS = (60, 180)

#: 壊れた zip の中身をログに出すバイト数。取得元のエラーページなら <title> まで入る
BROKEN_HEAD_BYTES = 400

#: abrg が取得する zip の一覧（DCAT）。壊れた zip の取得元 URL を引くのに使う
ABR_FEED_URL = "https://dataset.address-br.digital.go.jp/api/feed/dcat-us/1.1.json"

#: abrg が名乗る User-Agent。取得元の応答を abrg と同じ条件で記録するために揃える
ABRG_USER_AGENT = "curl/7.81.0"

#: 取得元の応答を記録する zip の数の上限
PROBE_LIMIT = 3

#: 東京都の全国地方公共団体コード62件。ABR の common.sqlite の city テーブルが正で、
#: `abrg download -c 130001` 後に `select lg_code from city order by lg_code` で取れる。
#: 都道府県コード 130001 を渡すと住居表示データが落ちてこず地番マスターだけになるので、
#: 市区町村コードを明示列挙する。
TOKYO_LG_CODES = [
    "131016", "131024", "131032", "131041", "131059", "131067", "131075", "131083",
    "131091", "131105", "131113", "131121", "131130", "131148", "131156", "131164",
    "131172", "131181", "131199", "131202", "131211", "131229", "131237", "132012",
    "132021", "132039", "132047", "132055", "132063", "132071", "132080", "132098",
    "132101", "132110", "132128", "132136", "132144", "132152", "132187", "132195",
    "132209", "132217", "132225", "132233", "132241", "132250", "132276", "132284",
    "132292", "133035", "133051", "133078", "133086", "133612", "133621", "133639",
    "133647", "133817", "133825", "134015", "134023", "134210",
]

#: 住所を持つ種別。data/ods/<id>.ndjson を読む
GEOCODED_DATASETS = [
    "aed", "bicycle_parking", "care_service", "cultural_property",
    "educational_institution", "evacuation_space", "event", "fire_hydrant",
    "food_business", "hospital", "polling_place", "preschool",
    "public_facility", "public_toilet", "public_wireless_lan", "tourism",
]

#: ODS 以外で住所を持つ NDJSON。address / _org_code / _org_title を ODS と同じ形で
#: 持つものだけをここに書く。結果は同じ addresses.ndjson に入り、
#: stg 側は ods と同じく (org_code, address) で引く
EXTRA_ADDRESS_FILES = [
    "data/hokenjo/food_establishment.ndjson",
    "data/hokenjo/sanitation_facility.ndjson",
]

#: address 列を持たない種別と、代わりに連結する列。
#: ここの構成は macros/ods_geo.sql の ods_address_key と一致させること。
#: 住所キーがずれると突合が丸ごと外れ、補完が静かに 0 件になる
ADDRESS_PARTS: dict[str, tuple[str, ...]] = {
    "educational_institution": ("city", "town", "street_number"),
}

#: 採用しない座標の粒度。city は市区町村の代表点で、地図に出すと区役所にピンが積み上がる。
#: prefecture も同じ理由。unknown は座標が無い
REJECTED_LEVELS = frozenset({"city", "prefecture", "unknown"})

#: 都道府県名。住所がこれで始まるなら自治体名の前置はしない
PREFECTURES = (
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県",
    "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県",
    "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県",
    "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県",
    "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
)



def _clean(value: object) -> str:
    """NDJSON の値を住所として扱える文字列にする。"""
    if value is None:
        return ""
    return str(value).strip()


def address_of(row: dict, dataset_id: str) -> str:
    """1行から住所文字列を取り出す。

    address 列を持つ種別はその値だけを使う。持たない種別だけ ADDRESS_PARTS の列を
    連結する。address が空の行に連結を代替させないのは、SQL 側の突合条件を
    単純に保つため（trim(address) だけで引ける）。
    """
    parts = ADDRESS_PARTS.get(dataset_id)
    if parts is None:
        return _clean(row.get("address"))
    return "".join(_clean(row.get(part)) for part in parts)


def normalize(text: str) -> str:
    """abr-geocoder が返す query.input と突き合わせるためのキー。

    abrg は入力を NFKC 正規化し連続空白を畳んで返すので、こちらも同じ形にする。
    生の文字列でキーにすると全角括弧を含む住所が軒並み外れる。
    """
    return " ".join(unicodedata.normalize("NFKC", text).split())


def geocode_input(address: str, org_title: str) -> str:
    """abr-geocoder に渡す住所。都道府県名・自治体名が無ければ前置する。

    自治体が公開する住所は自分の市区町村名から始まらないことがあり、そのままでは
    市区町村の代表点までしか解決しない。東京都の局が公開したデータの org_title は
    「東京都デジタルサービス局」のような部局名なので、市区町村名としては使わない。

    すでに都道府県名で始まる住所には何も足さない。区市町村は都外に保養所などを持って
    おり、前置すると「東京都新宿区山梨県北杜市…」という存在しない住所ができる。
    前置した自治体の町字と偶然一致すれば、全く別の場所の座標を採用してしまう。
    """
    address = address.strip()
    if address.startswith(PREFECTURES):
        return address
    if org_title.endswith(("区", "市", "町", "村")) and not address.startswith(org_title):
        address = org_title + address
    return "東京都" + address


def address_sources(ods_dir: Path, extra_files: list[str]) -> list[tuple[Path, str]]:
    """住所を読む NDJSON と、その種別 ID の組を並べる。

    種別 ID は ADDRESS_PARTS を引くためだけに使う。ODS 以外のファイルは
    address 列を持つ前提なので、ファイル名をそのまま種別 ID にしてよい。
    """
    sources = [(ods_dir / f"{d}.ndjson", d) for d in GEOCODED_DATASETS]
    sources += [(Path(p), Path(p).stem) for p in extra_files]
    return sources


def collect_addresses(
    ods_dir: Path, extra_files: list[str] | None = None
) -> dict[tuple[str, str], str]:
    """NDJSON から (組織コード, 住所) → abrg に渡す住所 を集める。"""
    collected: dict[tuple[str, str], str] = {}
    for path, dataset_id in address_sources(ods_dir, extra_files or []):
        if not path.exists():
            logger.warning("  %s: NDJSON が無いので飛ばす", dataset_id)
            continue
        with path.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                address = address_of(row, dataset_id)
                if not address:
                    continue
                key = (_clean(row.get("_org_code")), address)
                if key not in collected:
                    collected[key] = geocode_input(address, _clean(row.get("_org_title")))
    return collected


def _node_major() -> int | None:
    node = shutil.which("node")
    if not node:
        return None
    try:
        out = subprocess.run([node, "--version"], capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, OSError):
        return None
    return int(out.stdout.strip().lstrip("v").split(".")[0])


def run_with_timeout(cmd: list[str], timeout: float) -> None:
    """コマンドを実行し、timeout 秒を超えたらプロセスグループごと止めて例外を投げる。

    npx は sh と node を子に持つので、subprocess.run の timeout では npx しか止まらず、
    実際に動いている node が残る。新しいセッションで起動してグループごと止める。
    """
    proc = subprocess.Popen(cmd, start_new_session=True)
    try:
        returncode = proc.wait(timeout=timeout)
    except BaseException:
        _kill_group(proc)
        raise
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd)


def _kill_group(proc: subprocess.Popen) -> None:
    """proc のプロセスグループに SIGTERM を送り、猶予のあと SIGKILL で残りを止める。"""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        if sig == signal.SIGTERM:
            try:
                proc.wait(timeout=KILL_GRACE)
            except subprocess.TimeoutExpired:
                pass
    proc.wait()


def _abrg(args: list[str], timeout: float) -> None:
    """abr-geocoder を npx 経由で実行する。"""
    run_with_timeout(
        ["npx", "--yes", f"@digital-go-jp/abr-geocoder@{ABRG_VERSION}", *args],
        timeout,
    )


def find_broken_zips(download_dir: Path) -> list[Path]:
    """download_dir に残った zip のうち、zip として読めないものを返す。

    abrg は取り込んだ zip を消すので、取得が正常に終わればここには何も残らない。
    残るのは取り込みに失敗したものと、打ち切りで書きかけになったもの。
    abrg は HTTP のステータスを見ずに応答をそのまま保存するので、取得元が
    エラーページを返すと HTML が .zip の名前で残る。
    """
    if not download_dir.is_dir():
        return []
    broken = []
    for path in sorted(download_dir.glob("*.zip")):
        with path.open("rb") as f:
            head = f.read(4)
        if head != b"PK\x03\x04" or not zipfile.is_zipfile(path):
            broken.append(path)
    return broken


def _printable(data: bytes) -> str:
    """バイト列を 1 行のログに出せる文字列にする。"""
    return data.decode("utf-8", errors="backslashreplace").replace("\n", "\\n")


def _report_broken(broken: list[Path]) -> None:
    """壊れた zip の名前・サイズ・先頭のバイト列をログに出す。先頭が同じものはまとめる。"""
    groups: dict[bytes, list[Path]] = {}
    for path in broken:
        with path.open("rb") as f:
            groups.setdefault(f.read(BROKEN_HEAD_BYTES), []).append(path)
    for head, paths in groups.items():
        logger.warning(
            "  zip として読めないファイル %d 個: %s",
            len(paths),
            ", ".join(f"{p.name} ({p.stat().st_size} bytes)" for p in paths),
        )
        logger.warning("    先頭 %d バイト: %s", len(head), _printable(head))


def _probe_source(names: list[str]) -> None:
    """壊れていた zip を取得元へ取りに行き、ステータスとヘッダーをログに残す。

    取得元がエラーを返す理由の手がかりを残すためだけに使う。ここでの失敗では止めない。
    """
    try:
        request = Request(ABR_FEED_URL, headers={"User-Agent": ABRG_USER_AGENT})
        with urlopen(request, timeout=60) as response:
            feed = json.load(response)
    except Exception as e:  # 手がかりを残すだけなので何が起きても続ける
        logger.warning("    取得元の一覧を読めない: %r", e)
        return
    urls: dict[str, list[str]] = {}
    for dataset in feed.get("dataset", []):
        for dist in dataset.get("distribution") or []:
            url = dist.get("accessURL") or ""
            if ".csv.zip" in url:
                urls.setdefault(url.rsplit("/", 1)[-1], []).append(url)
    for name in names[:PROBE_LIMIT]:
        for url in urls.get(name, []):
            _probe_url(url)


def _probe_url(url: str) -> None:
    """url を GET し、ステータス・主要なヘッダー・本文の先頭をログに出す。

    手がかりを残すだけなので、接続から本文の読み取りまでのどこで失敗しても
    例外を外に出さない。取り直しの途中で呼ばれるので、ここで落ちると取り直しごと止まる。
    """
    request = Request(url, headers={"User-Agent": ABRG_USER_AGENT})
    try:
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as e:
            response = e
        with response:
            head = response.read(BROKEN_HEAD_BYTES)
            headers = {
                key: response.headers.get(key)
                for key in (
                    "Content-Type", "Content-Length", "Server",
                    "X-Cache", "X-Amz-Cf-Pop", "X-Amz-Cf-Id", "Retry-After",
                )
                if response.headers.get(key) is not None
            }
            status = response.status
    except Exception as e:
        logger.warning("    再取得 %s: %r", url, e)
        return
    logger.warning("    再取得 %s: HTTP %s %s", url, status, headers)
    if head[:4] != b"PK\x03\x04":
        logger.warning("      本文の先頭: %s", _printable(head))


def download_abr(
    abrg_dir: Path, retry_waits: tuple[float, ...] = DOWNLOAD_RETRY_WAITS
) -> None:
    """東京都62市区町村の ABR データを取得する。

    取得後に zip として読めないファイルが残っていれば、その中身をログに出し、
    間隔を空けて取り直す。abrg は壊れたファイルを飛ばしたあと止まることがあるので、
    打ち切られた場合も同じく壊れたファイルを探す。
    """
    abrg_dir.mkdir(parents=True, exist_ok=True)
    download_dir = abrg_dir / "download"
    attempts = len(retry_waits) + 1
    broken: list[Path] = []
    for attempt in range(1, attempts + 1):
        error: Exception | None = None
        try:
            # スレッド既定だと複数ワーカーが同じ sqlite を掴んで SQLITE_BUSY で即死するので
            # 1 に固定する
            _abrg(
                ["download", "-c", *TOKYO_LG_CODES, "-d", str(abrg_dir), "-t", "1", "--silent"],
                DOWNLOAD_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            error = e

        broken = find_broken_zips(download_dir)
        if not broken:
            if error is None:
                return
            raise SystemExit(f"ABR データの取得に失敗した: {error}") from error

        logger.warning(
            "  ABR データの取得 %d/%d 回目: zip でないファイルが %d 個残った%s",
            attempt, attempts, len(broken),
            f"（abrg: {type(error).__name__}）" if error else "",
        )
        _report_broken(broken)
        _probe_source([p.name for p in broken])
        for path in broken:
            path.unlink()
        if attempt < attempts:
            wait = retry_waits[attempt - 1]
            logger.warning("  %s 秒待って取り直す", wait)
            time.sleep(wait)

    raise SystemExit(
        f"ABR データの取得で zip でないファイルが {attempts} 回続けて返った: "
        + ", ".join(p.name for p in broken)
    )


def run_geocoder(abrg_dir: Path, input_path: Path, output_path: Path) -> None:
    """住所ファイルをジオコーディングする。

    target=residential は地番マスターを使わない指定。地番を使うと解決が地番側に
    寄って街区の解決を奪い、住居表示の採用がかえって減る。ライセンスの面でも
    登記所備付地図データ利用規約に触れずに済む。
    """
    _abrg(
        [
            str(input_path), str(output_path),
            "-d", str(abrg_dir), "-f", "ndjson",
            "--target", "residential", "--silent",
        ],
        GEOCODE_TIMEOUT,
    )


def geocode(
    ods_dir: str = "data/ods",
    dest_dir: str = "data/geocode",
    *,
    extra_files: list[str] | None = None,
    skip_download: bool = False,
) -> None:
    """住所をジオコーディングして NDJSON に出力する。"""
    node_major = _node_major()
    if node_major is None:
        raise SystemExit("node が見つからない。abr-geocoder の実行には Node.js 22 が要る")
    if node_major >= 24:
        raise SystemExit(
            f"Node.js {node_major} では abr-geocoder の依存 better-sqlite3 がビルドできない。"
            "Node.js 22 を使うこと"
        )

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    abrg_dir = dest / "abrg"
    input_path = dest / "input.txt"
    raw_output = dest / "abrg_output.ndjson"

    collected = collect_addresses(
        Path(ods_dir), EXTRA_ADDRESS_FILES if extra_files is None else extra_files
    )
    logger.info("  住所 %d 件（組織コード×住所）", len(collected))
    if not collected:
        raise SystemExit("ジオコーディング対象の住所が 1 件も無い")

    # abrg には重複を除いた住所だけ渡す
    queries = sorted(set(collected.values()))
    input_path.write_text("\n".join(queries) + "\n", encoding="utf-8")
    logger.info("  abrg へ渡す住所 %d 件", len(queries))

    if not skip_download:
        logger.info("  ABR データ取得（東京都62市区町村）")
        download_abr(abrg_dir)
    logger.info("  ジオコーディング実行")
    run_geocoder(abrg_dir, input_path, raw_output)

    results = _load_results(raw_output)
    _write(dest / "addresses.ndjson", collected, results)


def _load_results(path: Path) -> dict[str, dict]:
    """abrg の出力を正規化キー → 結果 に読み込む。"""
    results: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            results[normalize(record["query"]["input"])] = record["result"]
    return results


def _write(
    path: Path,
    collected: dict[tuple[str, str], str],
    results: dict[str, dict],
) -> None:
    """(組織コード, 住所) 単位の結果を NDJSON に書く。"""
    levels: Counter[str] = Counter()
    unresolved: list[str] = []
    adopted = 0

    with path.open("w", encoding="utf-8") as f:
        for (org_code, address), query in sorted(collected.items()):
            result = results.get(normalize(query))
            if result is None:
                # abrg は入力と同じ件数を返さない。隣接する2行を連結して1クエリに
                # してしまうバグがあり、連結された側は結果が返らない。黙って落とさず
                # 件数を数える
                unresolved.append(query)
                levels["(結果なし)"] += 1
                continue
            level = result.get("coordinate_level") or "unknown"
            levels[level] += 1
            usable = level not in REJECTED_LEVELS and result.get("lat") is not None
            if usable:
                adopted += 1
            f.write(json.dumps({
                "org_code": org_code,
                "address": address,
                "geo_lat": result["lat"] if usable else None,
                "geo_lon": result["lon"] if usable else None,
                "geo_level": level if usable else None,
                "lg_code": result.get("lg_code"),
                "machiaza_id": result.get("machiaza_id"),
                "pref": result.get("pref"),
                "city": result.get("city"),
                "ward": result.get("ward"),
                "oaza_cho": result.get("oaza_cho"),
                "chome": result.get("chome"),
                "koaza": result.get("koaza"),
                "blk_num": result.get("blk_num"),
                "rsdt_num": result.get("rsdt_num"),
                "rsdt_num2": result.get("rsdt_num2"),
                "match_level": result.get("match_level"),
            }, ensure_ascii=False) + "\n")

    total = len(collected)
    logger.info("  採用 %d / %d (%.1f%%)", adopted, total, 100 * adopted / total)
    for level, count in levels.most_common():
        logger.info("    %-20s %6d (%.1f%%)", level, count, 100 * count / total)
    if unresolved:
        logger.warning("  abrg が結果を返さなかった住所 %d 件", len(unresolved))
        for query in unresolved[:5]:
            logger.warning("    %s", query)
