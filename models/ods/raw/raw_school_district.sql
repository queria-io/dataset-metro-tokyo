{# 自治体標準ODS「小中学校通学区域情報」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/school_district.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/school_district.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'school_id': 'VARCHAR',
        'school_code': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'district': 'VARCHAR',
        'city': 'VARCHAR',
        'ward': 'VARCHAR',
        'school_municipality_code': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'poi_code': 'VARCHAR',
        'registered_date': 'VARCHAR',
        'abolished_date': 'VARCHAR',
        'district_addresses': 'VARCHAR',
        'notes': 'VARCHAR',
        'polygon_file': 'VARCHAR',
        '_extras': 'JSON',
        '_package_id': 'VARCHAR',
        '_resource_id': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR',
        '_fetched_at': 'VARCHAR'
    }
)
