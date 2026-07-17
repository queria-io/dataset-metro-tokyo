{# 自治体標準ODS「公衆トイレ一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/public_toilet.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/public_toilet.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'install_position': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'male_total': 'VARCHAR',
        'female_total': 'VARCHAR',
        'unisex_total': 'VARCHAR',
        'barrier_free_total': 'VARCHAR',
        'wheelchair': 'VARCHAR',
        'baby_facility': 'VARCHAR',
        'ostomate': 'VARCHAR',
        'start_time': 'VARCHAR',
        'end_time': 'VARCHAR',
        'available_notes': 'VARCHAR',
        'image': 'VARCHAR',
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
