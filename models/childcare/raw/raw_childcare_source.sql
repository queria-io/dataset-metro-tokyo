{# 子育て施設データの取得元（1行=1ファイル）。
   一覧は年2回の更新でパッケージ ID も配布ファイル名も変わるため、
   pipelines/childcare.py が解決した版と URL を data/childcare/source.ndjson に記録する。 #}

{{ config(materialized='table') }}

select *
from read_json(
    'data/childcare/source.ndjson',
    format='newline_delimited',
    columns={
        'file': 'VARCHAR',
        'edition': 'VARCHAR',
        'package_id': 'VARCHAR',
        'package_title': 'VARCHAR',
        'resource_name': 'VARCHAR',
        'url': 'VARCHAR',
        'fetched_at': 'VARCHAR'
    }
)
