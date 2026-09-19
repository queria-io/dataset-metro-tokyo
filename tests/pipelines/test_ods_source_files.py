"""台帳 (source_files.ndjson) に実際に書かれる行を確かめる。

classify() の戻り値ではなく、download_and_normalize() が書くファイルを読む。
reason の文字列形式は source_files.table.yml の列説明で利用者に約束している内容なので、
戻り値だけを見ていると形式を壊してもテストが緑のままになる。

取得はモックする。ネットワークにも DuckLake にもつながない。
"""

import json
from unittest.mock import patch

import yaml

from pipelines import ods

ORG = {"name": "t132128", "title": "日野市"}


def write_config(tmp_path):
    """AED 1種別だけの ods_datasets.yml を書く。"""
    path = tmp_path / "ods_datasets.yml"
    path.write_text(
        yaml.safe_dump(
            {
                "datasets": [
                    {
                        "id": "aed",
                        "title": "AED設置箇所一覧",
                        "slug_patterns": ["aed"],
                        "title_patterns": ["AED設置箇所"],
                        "columns": [
                            {"key": "name", "source": ["名称"]},
                            {"key": "address", "source": ["住所"]},
                        ],
                    }
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return str(path)


def write_packages(tmp_path, packages):
    path = tmp_path / "packages.ndjson"
    path.write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in packages),
        encoding="utf-8",
    )
    return str(path)


def run(tmp_path, packages):
    """取得を行わずに download_and_normalize を回し、台帳の行を返す。"""
    dest = tmp_path / "out"
    with patch.object(ods, "_fetch", side_effect=RuntimeError("no network in test")):
        ods.download_and_normalize(
            config_path=write_config(tmp_path),
            packages_path=write_packages(tmp_path, packages),
            dest_dir=str(dest),
        )
    lines = (dest / "source_files.ndjson").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def package(resources, package_id="pkg-1", title="AED設置箇所一覧"):
    return {
        "id": package_id,
        "title": title,
        "license_id": "CC-BY-4.0",
        "organization": dict(ORG),
        "resources": resources,
    }


def test_package_without_csv_leaves_one_row(tmp_path):
    rows = run(
        tmp_path,
        [
            package(
                [
                    {"id": "r1", "name": "AED一覧", "format": "HTML",
                     "url": "https://example.jp/132128_aed.html"},
                    {"id": "r2", "name": "AED一覧", "format": "PDF",
                     "url": "https://example.jp/132128_aed.pdf"},
                ]
            )
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["dataset_id"] == "aed"
    assert row["package_id"] == "pkg-1"
    assert row["org_code"] == "t132128"
    assert row["status"] == "skipped"
    assert row["reason"] == "no_csv_resource: formats=HTML,PDF"
    # リソースが存在しない行なので、リソース側の列は空にする
    assert row["resource_id"] is None
    assert row["resource_name"] is None
    assert row["url"] is None


def test_package_with_csv_still_goes_through_fetch(tmp_path):
    """CSV があるパッケージは従来どおり取得経路に進む（ここでは取得が失敗する）。"""
    rows = run(
        tmp_path,
        [
            package(
                [{"id": "r1", "name": "AED一覧", "format": "CSV",
                  "url": "https://example.jp/132128_aed.csv"}]
            )
        ],
    )

    assert len(rows) == 1
    assert rows[0]["status"] == "failed"
    assert rows[0]["reason"].startswith("fetch_error:")
    assert rows[0]["resource_id"] == "r1"
    assert rows[0]["url"] == "https://example.jp/132128_aed.csv"


def test_unmatched_package_leaves_no_row(tmp_path):
    rows = run(
        tmp_path,
        [
            package(
                [{"id": "r1", "name": "予算", "format": "PDF",
                  "url": "https://example.jp/yosan.pdf"}],
                title="予算書",
            )
        ],
    )

    assert rows == []
