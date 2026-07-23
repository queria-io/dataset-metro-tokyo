-- 【任意・メイン判断で採否】地域・年齢別人口の縦持ち（ロング）ビュー。
-- population（ワイド46列）を UNPIVOT し 1行 = 地域 × 調査年月日 × 年齢階級 × 性別 → 人口。
-- 年齢階級別の集計・可視化を容易にするための補助モデル（本体 population とは別に提供）。

{{ config(materialized='view') }}

with long as (
    unpivot {{ ref('population') }}
    on
        age_0_4_male,
        age_0_4_female,
        age_5_9_male,
        age_5_9_female,
        age_10_14_male,
        age_10_14_female,
        age_15_19_male,
        age_15_19_female,
        age_20_24_male,
        age_20_24_female,
        age_25_29_male,
        age_25_29_female,
        age_30_34_male,
        age_30_34_female,
        age_35_39_male,
        age_35_39_female,
        age_40_44_male,
        age_40_44_female,
        age_45_49_male,
        age_45_49_female,
        age_50_54_male,
        age_50_54_female,
        age_55_59_male,
        age_55_59_female,
        age_60_64_male,
        age_60_64_female,
        age_65_69_male,
        age_65_69_female,
        age_70_74_male,
        age_70_74_female,
        age_75_79_male,
        age_75_79_female,
        age_80_84_male,
        age_80_84_female,
        age_85over_male,
        age_85over_female
    into
        name age_sex
        value count
)

select
    municipality_code,
    prefecture,
    city,
    organization_name,
    survey_date,
    area_name,
    -- age_sex 例: 'age_0_4_male' → age_band='0-4'、'age_85over_female' → age_band='85+'
    case
        when age_sex like 'age_85over%' then '85+'
        else replace(regexp_replace(regexp_replace(age_sex, '^age_', ''), '_(male|female)$', ''), '_', '-')
    end as age_band,
    case when age_sex like '%_male' then '男性' else '女性' end as sex,
    count as population
from long
