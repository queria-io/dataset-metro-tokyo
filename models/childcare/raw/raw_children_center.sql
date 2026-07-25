{# 東京都福祉局「社会福祉施設等一覧」の児童館 CSV。
   pipelines/childcare.py がカタログのメタデータから最新版を解決し、
   cp932 → UTF-8 変換して data/childcare/children_center.csv に保存する。
   取り込んだ版は raw_childcare_source を参照。 #}

{{ config(materialized='table') }}

select *
from read_csv(
    'data/childcare/children_center.csv',
    header=true,
    all_varchar=true
)
