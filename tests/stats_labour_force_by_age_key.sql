{# 1行 = 年 × 男女 × 年齢階級 × 区分であること、各年・年齢階級・区分に男女計・男・女の3行がそろうこと、
   毎年 7 つの年齢階級に、就業率を除く 7 区分（2008年からは就業率を含む 8 区分）がそろうことを確かめる。 #}

with by_key as (
    select year, sex, age_group, item, count(*) as row_count
    from {{ ref('labour_force_by_age') }}
    group by all
),

by_item as (
    select year, age_group, item, count(*) as sex_count
    from by_key
    group by all
),

by_year as (
    select year, count(*) as cell_count
    from by_item
    group by year
)

select year, sex, age_group, item, 'duplicate' as check_name
from by_key
where row_count > 1
union all
select year, null, age_group, item, 'missing sex' as check_name
from by_item
where sex_count <> 3
union all
select year, null, null, null, 'missing cell' as check_name
from by_year
where cell_count <> case when year >= 2008 then 7 * 8 else 7 * 7 end
