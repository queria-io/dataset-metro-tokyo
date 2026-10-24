"""東京都「毎月勤労統計調査」年報の月間現金給与額のダウンロード。

東京都総務局統計部が公表する毎月勤労統計調査（地方調査）の年報から、
第1-1表（事業所規模5人以上）と第1-2表（事業所規模30人以上）の
「産業、性別常用労働者の1人平均月間現金給与額」を取り込む。

年報の CSV は 1行 = 事業所規模 × 産業 × 年 × 年平均・月 で、公表年の各月と年平均に
加えて過去数年分の年平均も載る。各年の値はその年の年報から取り、過去年の行は使わない。
年報の一覧ページから各年のページを、各年のページから CSV のリンクを解決する
（ファイル名の付け方が年によって違うため固定しない）。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index.htm
"""

import csv
import json
import logging
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines")

USER_AGENT = "dataset-metro-tokyo"

INDEX_URL = "https://www.toukei.metro.tokyo.lg.jp/maikin/mk-index2.htm"

# 年報のページ（/maikin/2025/mk25q30000.htm など）
_REPORT_LINK_RE = re.compile(r'href="(/maikin/(\d{4})/[^"]+\.htm)"[^>]*>\s*年報\s*<')
_CSV_LINK_RE = re.compile(r'href="([^"]+\.csv)"', re.IGNORECASE)

# 年報のページに並ぶ CSV の (並び位置, 表番号)。先頭2つが第1-1表と第1-2表。表題の行で確かめる
_TABLES = [(0, "第1-1表"), (1, "第1-2表")]

_HEADER = [
    "事業所規模",
    "産業",
    "和暦年",
    "西暦年",
    "年平均・月",
    "現金給与総額／計(円)",
    "現金給与総額／男(円)",
    "現金給与総額／女(円)",
    "きまって支給する給与／計(円)",
    "きまって支給する給与／男(円)",
    "きまって支給する給与／女(円)",
    "所定内給与(円)",
    "所定外給与(円)",
    "特別に支払われた給与／計(円)",
    "特別に支払われた給与／男(円)",
    "特別に支払われた給与／女(円)",
]
_VALUE_KEYS = [
    "cash_earnings",
    "cash_earnings_male",
    "cash_earnings_female",
    "contractual_earnings",
    "contractual_earnings_male",
    "contractual_earnings_female",
    "scheduled_earnings",
    "overtime_earnings",
    "special_earnings",
    "special_earnings_male",
    "special_earnings_female",
]

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_earnings.ndjson"


def _fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8-sig")


def _normalize(text: str) -> str:
    """全角の数字・記号を半角にそろえる（「５人以上」「第１－１表」など）。"""
    text = unicodedata.normalize("NFKC", text)
    return text.replace("ー", "-").replace("－", "-").strip()


def _report_pages(index_html: str) -> list[tuple[int, str]]:
    """年報の一覧ページから (公表年, ページ URL) を取り出す。"""
    pages = {
        int(year): urljoin(INDEX_URL, path)
        for path, year in _REPORT_LINK_RE.findall(index_html)
    }
    return sorted(pages.items())


def _table_name(rows: list[list[str]]) -> str | None:
    """CSV の末尾に置かれた表題の行から「第1-1表」「第3表」などを取り出す。"""
    for row in rows:
        if not row:
            continue
        matched = re.match(r"第\d+(?:-\d+)?表", _normalize(row[0]))
        if matched:
            return matched.group(0)
    return None


def _parse(
    text: str,
    report_year: int,
    header: list[str] = _HEADER,
    value_keys: list[str] = _VALUE_KEYS,
) -> list[dict]:
    """年報の CSV から公表年の行（各月と年平均）を取り出す。

    表末尾の空行・表題の行は西暦年が数字でないので落ちる。値は原典の文字列のまま
    （「×」は秘匿、「－」は該当なし）。調査産業計だけの表（第3表など）は産業の列が無く、
    industry を出力しない。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    if headers != header:
        raise ValueError(f"ヘッダーを認識できません: {headers}")

    with_industry = header[1] == "産業"
    key_count = 5 if with_industry else 4
    records = []
    for row in rows[1:]:
        if len(row) < len(header):
            continue
        keys = [v.strip() for v in row[:key_count]]
        size, year, period = keys[0], keys[-2], keys[-1]
        if not year.isdigit() or int(year) != report_year:
            continue
        values = [v.strip() for v in row[key_count : len(header)]]
        record = {
            "report_year": str(report_year),
            "establishment_size": _normalize(size),
        }
        if with_industry:
            record["industry"] = keys[1]
        records.append(
            {
                **record,
                "year": year,
                "period": period,
                **dict(zip(value_keys, values, strict=True)),
            }
        )
    return records


def download_annual_tables(
    dest_dir: str,
    tables: list[tuple[int, str]],
    header: list[str],
    value_keys: list[str],
    output_filename: str,
) -> None:
    """各年の年報から指定の表を取得し、公表年の行を NDJSON に出力する。

    tables は年報のページに並ぶ CSV の (並び位置, 表番号)。表番号は CSV の表題の行で確かめる。
    取り込んだ年報・表・URL・行数は source.ndjson に記録する。
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = _report_pages(_fetch(INDEX_URL))
    if not pages:
        raise RuntimeError(f"年報のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, page_url in pages:
        links = _CSV_LINK_RE.findall(_fetch(page_url))
        for position, expected in tables:
            url = urljoin(page_url, links[position])
            text = _fetch(url)
            table = _table_name(list(csv.reader(text.splitlines())))
            if table != expected:
                raise RuntimeError(f"{url} は {expected} ではありません（{table}）")
            parsed = _parse(text, report_year, header, value_keys)
            if not parsed:
                raise RuntimeError(f"{report_year}年の行を取り出せません: {url}")
            records.extend(parsed)
            sources.append(
                {
                    "report_year": str(report_year),
                    "table": table,
                    "url": url,
                    "fetched_at": fetched_at,
                    "row_count": len(parsed),
                }
            )

    with (dest / output_filename).open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with (dest / _SOURCE_FILENAME).open("w", encoding="utf-8") as f:
        for entry in sources:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        f"  {Path(output_filename).stem}: {len(records)} rows"
        f" / {pages[0][0]}-{pages[-1][0]}"
    )


def download_labour_earnings(dest_dir: str) -> None:
    """各年の年報から第1-1表・第1-2表を取得し、公表年の行を NDJSON に出力する。"""
    download_annual_tables(dest_dir, _TABLES, _HEADER, _VALUE_KEYS, _OUTPUT_FILENAME)
