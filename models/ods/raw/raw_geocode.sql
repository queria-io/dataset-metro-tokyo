{# ODS の住所をジオコーディングした結果の生データ。
   pipelines/geocode.py が abr-geocoder の出力を (組織コード, 住所) 単位にまとめて
   data/geocode/addresses.ndjson に保存する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/geocode/addresses.ndjson',
    format='newline_delimited',
    columns={
        'org_code': 'VARCHAR',
        'address': 'VARCHAR',
        'geo_lat': 'DOUBLE',
        'geo_lon': 'DOUBLE',
        'geo_level': 'VARCHAR',
        'lg_code': 'VARCHAR',
        'machiaza_id': 'VARCHAR',
        'pref': 'VARCHAR',
        'city': 'VARCHAR',
        'ward': 'VARCHAR',
        'oaza_cho': 'VARCHAR',
        'chome': 'VARCHAR',
        'koaza': 'VARCHAR',
        'blk_num': 'VARCHAR',
        'rsdt_num': 'VARCHAR',
        'rsdt_num2': 'VARCHAR',
        'match_level': 'VARCHAR'
    }
)
