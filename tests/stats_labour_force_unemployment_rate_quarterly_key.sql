{# 1行 = 四半期 × 地域 × 男女であること、各四半期に 3地域 × 3区分がそろうこと、
   完全失業率が空でないことを確かめる。 #}

with by_key as (
    select year, quarter, area, sex, count(*) as row_count, count(unemployment_rate) as value_count
    from {{ ref('labour_force_unemployment_rate_quarterly') }}
    group by all
),

by_quarter as (
    select year, quarter, count(*) as key_count
    from by_key
    group by all
)

select year, quarter, area, sex, 'duplicate or null' as check_name
from by_key
where row_count > 1 or value_count < row_count
union all
select year, quarter, null, null, 'missing area or sex' as check_name
from by_quarter
where key_count <> 9
