{# 自治体標準ODS「投票所一覧」（期日前投票所を含む）の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/polling_place.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/polling_place.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'organization_name': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'polling_place_id': 'VARCHAR',
        'voting_district_number': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'name_en': 'VARCHAR',
        'description': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'ward': 'VARCHAR',
        'town': 'VARCHAR',
        'town_id': 'VARCHAR',
        'street_number': 'VARCHAR',
        'building_name': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'crs': 'VARCHAR',
        'crs_code': 'VARCHAR',
        'polling_place_type': 'VARCHAR',
        'voting_district': 'VARCHAR',
        'election_type': 'VARCHAR',
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
