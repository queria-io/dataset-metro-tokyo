{# 自治体標準ODS「指定緊急避難場所一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/evacuation_space.ndjson に
   保存する。型変換は stg で行うため全列 VARCHAR、マッピング外の列は _extras (JSON)。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/evacuation_space.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'elevation': 'VARCHAR',
        'for_flood': 'VARCHAR',
        'for_landslide': 'VARCHAR',
        'for_storm_surge': 'VARCHAR',
        'for_earthquake': 'VARCHAR',
        'for_tsunami': 'VARCHAR',
        'for_large_fire': 'VARCHAR',
        'for_inland_flooding': 'VARCHAR',
        'for_volcano': 'VARCHAR',
        'shelter_overlap': 'VARCHAR',
        'capacity_note': 'VARCHAR',
        'target_area': 'VARCHAR',
        'url': 'VARCHAR',
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
