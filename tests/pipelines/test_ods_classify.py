"""classify() の種別照合と、CSV が無いパッケージの台帳記録。

取り込みの挙動を公開せずに確かめるための単体テスト。packages.ndjson の小さな
実例を組み立てて classify() に渡す（ネットワークも DuckLake も要らない）。
"""

import json

from pipelines.ods import OdsDataset, classify

ALLOWED_LICENSE = "CC-BY-4.0"


def make_dataset(dataset_id="aed", slugs=None, titles=None) -> OdsDataset:
    return OdsDataset(
        id=dataset_id,
        title="AED設置箇所一覧",
        slug_patterns=slugs if slugs is not None else [dataset_id],
        title_patterns=titles if titles is not None else [],
        header_map={},
        required_columns=[],
        identity_column="name",
    )


def make_package(resources, package_id="pkg-1", title="AED設置箇所一覧", license_id=ALLOWED_LICENSE):
    return {
        "id": package_id,
        "title": title,
        "license_id": license_id,
        "organization": {"name": "t132128", "title": "日野市"},
        "resources": resources,
    }


def resource(url, fmt, resource_id="res-1", name="リソース"):
    return {"id": resource_id, "name": name, "url": url, "format": fmt}


def write_packages(tmp_path, packages):
    path = tmp_path / "packages.ndjson"
    path.write_text(
        "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in packages),
        encoding="utf-8",
    )
    return str(path)


def test_csv_resource_becomes_target(tmp_path):
    path = write_packages(
        tmp_path,
        [make_package([resource("https://example.jp/132128_aed.csv", "CSV")])],
    )
    targets, no_csv = classify(path, [make_dataset()])

    assert [t[2]["id"] for t in targets] == ["res-1"]
    assert no_csv == []


def test_package_matched_by_slug_but_only_html_is_recorded(tmp_path):
    """HTML でしか登録されていないパッケージが台帳から消えないこと。"""
    path = write_packages(
        tmp_path,
        [make_package([resource("https://example.jp/132128_aed.html", "HTML")])],
    )
    targets, no_csv = classify(path, [make_dataset()])

    assert targets == []
    assert len(no_csv) == 1
    dataset, package, formats = no_csv[0]
    assert dataset.id == "aed"
    assert package["id"] == "pkg-1"
    assert formats == ["HTML"]


def test_package_matched_by_title_but_no_csv_is_recorded(tmp_path):
    """副判定（タイトル）だけで一致した場合も記録する。"""
    path = write_packages(
        tmp_path,
        [
            make_package(
                [resource("https://example.jp/shiryo.pdf", "PDF")],
                title="AED設置箇所一覧",
            )
        ],
    )
    targets, no_csv = classify(path, [make_dataset(slugs=["aed"], titles=["AED設置箇所"])])

    assert targets == []
    assert [f for _, _, f in no_csv] == [["PDF"]]


def test_formats_are_deduplicated_and_sorted(tmp_path):
    path = write_packages(
        tmp_path,
        [
            make_package(
                [
                    resource("https://example.jp/132128_aed.html", "HTML", "r1"),
                    resource("https://example.jp/a.pdf", "PDF", "r2"),
                    resource("https://example.jp/b.html", "HTML", "r3"),
                    resource("https://example.jp/c", "", "r4"),
                ]
            )
        ],
    )
    _, no_csv = classify(path, [make_dataset()])

    assert no_csv[0][2] == ["HTML", "PDF", "UNKNOWN"]


def test_package_with_both_csv_and_html_is_not_recorded_as_missing(tmp_path):
    """CSV が1つでも取れるなら台帳の行は取得結果の側に立つ。"""
    path = write_packages(
        tmp_path,
        [
            make_package(
                [
                    resource("https://example.jp/132128_aed.html", "HTML", "r1"),
                    resource("https://example.jp/132128_aed.csv", "CSV", "r2"),
                ]
            )
        ],
    )
    targets, no_csv = classify(path, [make_dataset()])

    assert [t[2]["id"] for t in targets] == ["r2"]
    assert no_csv == []


def test_csv_without_format_declaration_is_detected_by_extension(tmp_path):
    path = write_packages(
        tmp_path,
        [make_package([resource("https://example.jp/132128_aed.csv", "")])],
    )
    targets, no_csv = classify(path, [make_dataset()])

    assert len(targets) == 1
    assert no_csv == []


def test_unmatched_package_is_not_recorded(tmp_path):
    """種別に一致しないパッケージまで載せない（台帳がカタログ全体に膨らむため）。"""
    path = write_packages(
        tmp_path,
        [make_package([resource("https://example.jp/yosan.pdf", "PDF")], title="予算書")],
    )
    targets, no_csv = classify(path, [make_dataset()])

    assert targets == []
    assert no_csv == []


def test_license_gate_still_precedes_matching(tmp_path):
    """ライセンスで落ちたパッケージは台帳に載せない。"""
    path = write_packages(
        tmp_path,
        [
            make_package(
                [resource("https://example.jp/132128_aed.html", "HTML")],
                license_id="CC-BY-NC-4.0",
            )
        ],
    )
    targets, no_csv = classify(path, [make_dataset()])

    assert targets == []
    assert no_csv == []


def test_same_package_is_recorded_once_per_dataset(tmp_path):
    """同じパッケージが複数のリソースで一致しても、種別ごとに1行だけにする。"""
    path = write_packages(
        tmp_path,
        [
            make_package(
                [
                    resource("https://example.jp/132128_aed.html", "HTML", "r1"),
                    resource("https://example.jp/132128_aed_2.html", "HTML", "r2"),
                ]
            )
        ],
    )
    _, no_csv = classify(path, [make_dataset()])

    assert len(no_csv) == 1


def test_duplicate_url_across_resources_yields_one_target(tmp_path):
    """同一 URL が複数リソースとして登録されていても取り込みは1件。"""
    url = "https://example.jp/132128_aed.csv"
    path = write_packages(
        tmp_path,
        [
            make_package(
                [resource(url, "CSV", "r1"), resource(url, "CSV", "r2")]
            )
        ],
    )
    targets, _ = classify(path, [make_dataset()])

    assert [t[2]["id"] for t in targets] == ["r1"]
