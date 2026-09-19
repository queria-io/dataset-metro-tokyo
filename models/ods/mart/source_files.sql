-- ODS 取り込みの実行結果（自治体別カバレッジと失敗理由の把握用）。
-- 基本は1行=1リソース。種別に一致しながら CSV リソースを持たないパッケージだけ、
-- パッケージ単位で1行（status=skipped / reason=no_csv_resource）になる
select
    dataset_id,
    org_code,
    org_title,
    package_id,
    package_title,
    resource_id,
    resource_name,
    url,
    status,
    reason,
    encoding,
    row_count,
    fetched_at
from {{ ref('stg_ods_source_files') }}
