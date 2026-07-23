{# 自治体標準ODS「ごみの分別方法一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/garbage_separation.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/garbage_separation.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'item_id': 'VARCHAR',
        'organization_name': 'VARCHAR',
        'collection_area': 'VARCHAR',
        'item_name': 'VARCHAR',
        'item_name_kana': 'VARCHAR',
        'item_name_en': 'VARCHAR',
        'separation_category': 'VARCHAR',
        'caution': 'VARCHAR',
        'fee_type': 'VARCHAR',
        'fee': 'VARCHAR',
        'bulky_fee': 'VARCHAR',
        'fee_notes': 'VARCHAR',
        'notes': 'VARCHAR',
        '_extras': 'JSON',
        '_package_id': 'VARCHAR',
        '_resource_id': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR',
        '_fetched_at': 'VARCHAR'
    }
)
