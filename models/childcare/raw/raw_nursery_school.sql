{# 東京都福祉局「社会福祉施設等一覧（令和7年5月1日時点）」の認可保育所 CSV。
   pipelines/childcare.py が cp932 → UTF-8 変換して data/childcare/nursery_school.csv に保存する。
   元データ: https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-1-hoikusyo.csv #}

{{ config(materialized='table') }}

select *
from read_csv(
    'data/childcare/nursery_school.csv',
    header=true,
    all_varchar=true
)
