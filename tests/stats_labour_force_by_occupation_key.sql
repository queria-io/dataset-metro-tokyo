{# 1行 = 年 × 男女 × 職業であること、各年に男女計・男・女 × 7職業の21行がそろうことを確かめる。 #}

with by_key as (
    select year, sex, occupation, count(*) as row_count
    from {{ ref('labour_force_by_occupation') }}
    group by all
),

by_year as (
    select year, count(*) as key_count
    from by_key
    group by year
)

select year, sex, occupation, 'duplicate' as check_name
from by_key
where row_count > 1
union all
select year, null, null, 'missing key' as check_name
from by_year
where key_count <> 21
