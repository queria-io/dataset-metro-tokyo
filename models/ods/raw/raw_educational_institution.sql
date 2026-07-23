{# 自治体標準ODS「教育機関一覧」の生データ。
   pipelines/ods.py が対象 CSV を標準キーに正規化して data/ods/educational_institution.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/ods/educational_institution.ndjson',
    format='newline_delimited',
    columns={
        'school_code': 'VARCHAR',
        'school_type': 'VARCHAR',
        'prefecture_code': 'VARCHAR',
        'establishment_category': 'VARCHAR',
        'establisher': 'VARCHAR',
        'branch_type': 'VARCHAR',
        'main_school_code': 'VARCHAR',
        'main_school_name': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'name_alias': 'VARCHAR',
        'city': 'VARCHAR',
        'town': 'VARCHAR',
        'street_number': 'VARCHAR',
        'postal_code': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'contact_name': 'VARCHAR',
        'phone_number': 'VARCHAR',
        'attribute_set_date': 'VARCHAR',
        'attribute_abolished_date': 'VARCHAR',
        'old_survey_number': 'VARCHAR',
        'new_school_code': 'VARCHAR',
        '_extras': 'JSON',
        '_package_id': 'VARCHAR',
        '_resource_id': 'VARCHAR',
        '_org_code': 'VARCHAR',
        '_org_title': 'VARCHAR',
        '_source_url': 'VARCHAR',
        '_fetched_at': 'VARCHAR'
    }
)
