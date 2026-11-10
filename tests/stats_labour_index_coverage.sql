{# 各年に 9 種類の指数がそろい、指数の種類 × 事業所規模 × 産業ごとに年平均と 12 か月の 13 行があることを確かめる。
   年報の CSV の並び位置がずれて別の表を読むと、種類が欠けるか重なる。 #}

with by_year as (
    select year, count(distinct index_type) as index_types
    from {{ ref('labour_index') }}
    group by year
),

by_series as (
    select index_type, year, establishment_size, industry_code, count(*) as periods
    from {{ ref('labour_index') }}
    group by all
)

select year, index_types, null as periods
from by_year
where index_types <> 9
union all
select year, null, periods
from by_series
where periods <> 13
