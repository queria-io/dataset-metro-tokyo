"""東京都「東京の労働力」年平均の第8表（年齢階級・雇用形態別の役員を除く雇用者数）のダウンロード。

東京の労働力の年平均の第8表は、役員を除く雇用者数（千人）を雇用形態（正規の職員・従業員／
非正規の職員・従業員）別・年齢階級別・男女別に持つ。2015年の表から載り、各年の表には
直近の3〜5年分が載るので、すべての年の表を取り込み、年ごとにどの年の表から取った値かを
残す。どの年の表の値を使うかは dbt 側で決める（基準人口の切り替えで後の年の表の値が
改訂されている）。

CSV の形は年で2通りある。

- 2015〜2020年の表: 1行 = 男女 × 雇用形態 × 年（「実数／男女計／正規／平成27年平均」）、
  列 = 年齢階級（「総数(千人)」「15～24歳(千人)」など）
- 2021年からの表: 1行 = 男女 × 年（「実数／男女計／令和７年」）、
  列 = 雇用形態 × 年齢階級（「正規／総数（千人）」など）

どちらも実数の行を雇用形態 × 年齢階級ごとの行に分ける。対前年増減数の行は実数の差なので
取り込まない。2020〜2022年の表は西暦の列が無いので、列は見出しで読む。

各年のページは一覧ページから、CSV は各年のページのリンクのうちファイル名が
0800.csv で終わるものから解決し、表題の行で第8表であることを確かめる。

データソース: 東京都の統計
https://www.toukei.metro.tokyo.lg.jp/roudou/rd-index.htm
"""

import csv
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from pipelines.labour_force import INDEX_URL
from pipelines.labour_force_unemployment_rate import (
    _annual_pages,
    _get,
    _normalize,
    _year,
)
from shared.fetch import replacing

logger = logging.getLogger("pipelines")

_FIRST_REPORT_YEAR = 2015
_CSV_LINK_RE = re.compile(r'href="([^"]+0800\.csv)"', re.IGNORECASE)
# 「第８表 年齢階級別雇用形態別の役員を除く雇用者数」（2015〜2016年の表）、
# 「第８表　年齢階級、雇用形態別の役員を除く雇用者数」（2017年の表から）
_TITLE_RE = re.compile(
    r"^第\s*8\s*表\s*年齢階級[別、,]\s*雇用形態別の役員を除く雇用者数$"
)
_SEXES = ("男女計", "男", "女")
_EMPLOYMENT_TYPES = ("正規", "非正規")
# NFKC 後の「正規/総数(千人)」「総数(千人)」
_VALUE_HEADER_RE = re.compile(r"^(?:(正規|非正規)/)?(.+)\(千人\)$")
_AGE_GROUPS = (
    "総数",
    "15～24歳",
    "25～34歳",
    "35～44歳",
    "45～54歳",
    "55～64歳",
    "65歳以上",
)

_SOURCE_FILENAME = "source.ndjson"
_OUTPUT_FILENAME = "labour_force_by_employment_type.ndjson"


def _is_employment_type_table(rows: list[list[str]]) -> bool:
    """CSV の末尾に置かれた表題の行が第8表かを見る。"""
    return any(row and _TITLE_RE.match(_normalize(row[0])) for row in rows)


def _columns(headers: list[str], first_value: int) -> list[tuple[str | None, str]]:
    """値の列の見出しを (雇用形態, 年齢階級) にする。雇用形態が行にある表では None。

    年齢階級は NFKC で「～」が「~」になるので、原典の「～」に戻す。
    """
    columns = []
    for header in headers[first_value:]:
        matched = _VALUE_HEADER_RE.match(_normalize(header))
        if not matched:
            raise ValueError(f"ヘッダーを認識できません: {headers}")
        employment_type, age_group = matched.groups()
        columns.append((employment_type, age_group.replace("~", "～")))

    types = {employment_type for employment_type, _ in columns}
    if types == {None}:
        expected = [(None, age) for age in _AGE_GROUPS]
    else:
        expected = [(t, age) for t in _EMPLOYMENT_TYPES for age in _AGE_GROUPS]
    if columns != expected:
        raise ValueError(f"ヘッダーを認識できません: {headers}")
    return columns


def _parse(text: str, report_year: int) -> list[dict]:
    """第8表の CSV から実数の行を取り出し、男女 × 年 × 雇用形態 × 年齢階級の行に分ける。

    雇用形態は「正規」「非正規」、値は原典の文字列のまま。
    """
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        raise ValueError("空のファイルです")
    headers = [h.strip() for h in rows[0]]
    has_western_year = len(headers) > 1 and _normalize(headers[1]).startswith("西暦")
    first_value = 2 if has_western_year else 1
    columns = _columns(headers, first_value)
    type_in_row = columns[0][0] is None

    records = []
    for row in rows[1:]:
        if not row or not row[0].strip().startswith("実数"):
            continue
        parts = row[0].strip().split("／")
        if len(parts) != (4 if type_in_row else 3) or parts[1] not in _SEXES:
            raise ValueError(f"男女と年を読み取れません: {row[0]}")
        sex = parts[1]
        row_type = parts[2] if type_in_row else None
        if type_in_row and row_type not in _EMPLOYMENT_TYPES:
            raise ValueError(f"雇用形態を読み取れません: {row[0]}")
        year = _year(parts[-1])
        if has_western_year and row[1].strip() != str(year):
            raise ValueError(f"和暦と西暦が合いません: {row[:2]}")
        values = row[first_value:]
        if len(values) != len(columns):
            raise ValueError(f"列の数が見出しと合いません: {row[0]}")
        for (column_type, age_group), value in zip(columns, values, strict=True):
            records.append(
                {
                    "report_year": str(report_year),
                    "year": str(year),
                    "sex": sex,
                    "employment_type": row_type or column_type,
                    "age_group": age_group,
                    "value": value.strip(),
                }
            )
    return records


def download_labour_force_by_employment_type(dest_dir: str) -> None:
    """各年の年平均のページから第8表を取得し、男女 × 年 × 雇用形態 × 年齢階級の行を NDJSON に出力する。"""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    pages = [
        (year, url)
        for year, url in _annual_pages(_get(INDEX_URL))
        if year >= _FIRST_REPORT_YEAR
    ]
    if not pages:
        raise RuntimeError(f"年平均のページを見つけられません: {INDEX_URL}")

    records = []
    sources = []
    fetched_at = datetime.now(UTC).isoformat()
    for report_year, page_url in pages:
        links = _CSV_LINK_RE.findall(_get(page_url))
        if len(links) != 1:
            raise RuntimeError(f"第8表の CSV を1つに決められません: {page_url} {links}")
        url = urljoin(page_url, links[0])
        text = _get(url)
        if not _is_employment_type_table(list(csv.reader(text.splitlines()))):
            raise RuntimeError(
                f"{url} は第8表（年齢階級・雇用形態別の役員を除く雇用者数）ではありません"
            )
        parsed = _parse(text, report_year)
        if not parsed:
            raise RuntimeError(f"{report_year}年の表から行を取り出せません: {url}")
        records.extend(parsed)
        sources.append(
            {
                "report_year": str(report_year),
                "url": url,
                "fetched_at": fetched_at,
                "row_count": len(parsed),
            }
        )

    with replacing(dest / _OUTPUT_FILENAME) as partial:
        with partial.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with replacing(dest / _SOURCE_FILENAME) as partial:
        with partial.open("w", encoding="utf-8") as f:
            for entry in sources:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info(
        f"  labour_force_by_employment_type: {len(records)} rows"
        f" / {pages[0][0]}-{pages[-1][0]}"
    )
