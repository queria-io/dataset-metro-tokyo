{# 住民基本台帳による世帯と人口のステージング。
   人口・世帯数を INTEGER に型変換し（原典の '-' は NULL）、月初日を DATE で付与する。

   原典の扱いに 3 つの癖があるためここで吸収する。
   1. 集計行（区部・市部・郡部・島部）は表の先頭と各ブロックの見出しに 2 回現れる。
      値は同じなので 月 × 地域コード で 1 行に落とす。
   2. 2001年分は西多摩郡の 4 町村の地域コードが 1 つずつずれており（檜原村と奥多摩町が
      同じ 13308）、郡の集計行が 13303（＝瑞穂町のコード）になっている。
      2002年1月分以降の原典と同じコードに直す。値は郡部の集計行と一致することを確認済み。
   3. 「地域階層」列の番号体系は 2020年1月〜2022年2月分だけ変わる（区市町村が 4 ではなく 5）。
      年による揺れがない地域コードから区分を導出する。 #}

with corrected as (
    select
        year_month,
        case
            when year_month < '2002-01' then
                case area_name
                    when '瑞穂町' then '13303'
                    when '日の出町' then '13305'
                    when '檜原村' then '13307'
                    when '奥多摩町' then '13308'
                    when '西多摩郡' then '13300'
                    else area_code
                end
            else area_code
        end as area_code,
        area_name,
        population_total,
        population_change,
        japanese_total,
        japanese_male,
        japanese_female,
        foreign_total,
        foreign_male,
        foreign_female,
        household_total,
        household_japanese_only,
        household_foreign_only,
        household_mixed
    from {{ ref('raw_resident_population') }}
)

select
    year_month,
    cast(year_month || '-01' as date) as as_of_date,
    area_code,
    area_name,
    case
        when area_code = '13000' then '総数'
        when area_code in ('13100', '13200', '13550', '13300', '13350') then '地域区分'
        when area_code in ('13360', '13380', '13400', '13420') then '支庁'
        else '区市町村'
    end as area_type,
    {{ stats_integer('population_total') }} as population_total,
    {{ stats_integer('population_change') }} as population_change,
    {{ stats_integer('japanese_total') }} as japanese_total,
    {{ stats_integer('japanese_male') }} as japanese_male,
    {{ stats_integer('japanese_female') }} as japanese_female,
    {{ stats_integer('foreign_total') }} as foreign_total,
    {{ stats_integer('foreign_male') }} as foreign_male,
    {{ stats_integer('foreign_female') }} as foreign_female,
    {{ stats_integer('household_total') }} as household_total,
    {{ stats_integer('household_japanese_only') }} as household_japanese_only,
    {{ stats_integer('household_foreign_only') }} as household_foreign_only,
    {{ stats_integer('household_mixed') }} as household_mixed
from corrected
{# 2011年10月分までは郡部の集計行がブロック見出しでは「西多摩郡」名で載る。
   現行の原典と同じ「郡部」を残す。 #}
qualify row_number() over (
    partition by year_month, area_code
    order by case when area_name = '西多摩郡' then 1 else 0 end
) = 1
