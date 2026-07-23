{# 自治体標準ODS「食品等営業許可・届出一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/food_business.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/food_business.ndjson',
    format='newline_delimited',
    columns={
        'municipality_code': 'VARCHAR',
        'facility_id': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'name_en': 'VARCHAR',
        'business_type': 'VARCHAR',
        'business_category': 'VARCHAR',
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
        'phone_number': 'VARCHAR',
        'email': 'VARCHAR',
        'contact_form_url': 'VARCHAR',
        'contact_notes': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'corporate_name': 'VARCHAR',
        'corporate_number': 'VARCHAR',
        'permit_number': 'VARCHAR',
        'first_permit_date': 'VARCHAR',
        'permit_date': 'VARCHAR',
        'permit_start_date': 'VARCHAR',
        'permit_expiry_date': 'VARCHAR',
        'closure_date': 'VARCHAR',
        'application_type': 'VARCHAR',
        'permit_condition': 'VARCHAR',
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
