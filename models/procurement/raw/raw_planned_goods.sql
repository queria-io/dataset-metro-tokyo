{# 区市町村が公表した物品買入れの発注予定の生データ（1行=1件）。
   pipelines/procurement.py が data/procurement/planned_goods.ndjson に書く。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/procurement/planned_goods.ndjson',
    format='newline_delimited',
    columns={
        'org_code': 'VARCHAR',
        'org_name': 'VARCHAR',
        'item_type': 'VARCHAR',
        'title': 'VARCHAR',
        'delivery_place': 'VARCHAR',
        'delivery_deadline': 'VARCHAR',
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
