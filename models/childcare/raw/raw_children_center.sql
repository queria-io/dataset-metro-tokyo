{# 東京都福祉局「社会福祉施設等一覧（令和7年5月1日時点）」の児童館 CSV。
   pipelines/childcare.py が cp932 → UTF-8 変換して data/childcare/children_center.csv に保存する。
   元データ: https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-2_06-zidoukan.csv #}

{{ config(materialized='table') }}

select *
from read_csv(
    'data/childcare/children_center.csv',
    header=true,
    all_varchar=true
)
