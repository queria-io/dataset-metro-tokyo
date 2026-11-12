{# 区市町村が公表した工事の発注予定の生データ（1行=1件）。
   pipelines/procurement.py が data/procurement/planned_works.ndjson に書く。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/procurement/planned_works.ndjson',
    format='newline_delimited',
    columns={
        'org_code': 'VARCHAR',
        'org_name': 'VARCHAR',
        'work_type': 'VARCHAR',
        'title': 'VARCHAR',
        'location': 'VARCHAR',
        'location_prefecture': 'VARCHAR',
        'location_city': 'VARCHAR',
        'location_town': 'VARCHAR',
        'location_block': 'VARCHAR',
        'location_building': 'VARCHAR',
        'lat': 'VARCHAR',
        'lon': 'VARCHAR',
        'period_start': 'VARCHAR',
        'period_end': 'VARCHAR',
        'summary': 'VARCHAR',
        'bidding_method': 'VARCHAR',
        'bidding_timing': 'VARCHAR',
        'note': 'VARCHAR',
        'category': 'VARCHAR',
        'period_label': 'VARCHAR',
        'source_resource': 'VARCHAR',
        'source_url': 'VARCHAR'
    }
)
