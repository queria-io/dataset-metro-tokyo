{# 自治体標準ODS「消防水利施設一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/fire_hydrant.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/fire_hydrant.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'organization_name': 'VARCHAR',
        'facility_type': 'VARCHAR',
        'location_municipality_code': 'VARCHAR',
        'town_id': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'town': 'VARCHAR',
        'street_number': 'VARCHAR',
        'building_name': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'diameter': 'VARCHAR',
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
