{# 自治体標準ODS「自転車駐車場一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/bicycle_parking.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/bicycle_parking.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'organization_name': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'name_en': 'VARCHAR',
        'name_alias': 'VARCHAR',
        'poi_code': 'VARCHAR',
        'address': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'building_name': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'indoor_outdoor': 'VARCHAR',
        'capacity': 'VARCHAR',
        'nearest_station': 'VARCHAR',
        'available_days': 'VARCHAR',
        'start_time': 'VARCHAR',
        'end_time': 'VARCHAR',
        'available_notes': 'VARCHAR',
        'fee_type': 'VARCHAR',
        'fee': 'VARCHAR',
        'fee_details': 'VARCHAR',
        'payment_type': 'VARCHAR',
        'opened_date': 'VARCHAR',
        'description': 'VARCHAR',
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
