{# 1行 = 年 × 地域 × 男女であること、各年に 3地域 × 3区分がそろうこと、
   完全失業率が空でないことを確かめる。 #}

with by_key as (
    select year, area, sex, count(*) as row_count, count(unemployment_rate) as value_count
    from {{ ref('labour_force_unemployment_rate') }}
    group by all
),

by_year as (
    select year, count(*) as key_count
    from by_key
    group by year
)

select year, area, sex, 'duplicate or null' as check_name
from by_key
where row_count > 1 or value_count < row_count
union all
select year, null, null, 'missing area or sex' as check_name
from by_year
where key_count <> 9
