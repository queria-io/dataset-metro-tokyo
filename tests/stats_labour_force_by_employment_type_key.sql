{# 1行 = 年 × 男女 × 雇用形態 × 年齢階級であること、各年に男女計・男・女 × 正規・非正規 ×
   7年齢階級の42行がそろうことを確かめる。 #}

with by_key as (
    select year, sex, employment_type, age_group, count(*) as row_count
    from {{ ref('labour_force_by_employment_type') }}
    group by all
),

by_year as (
    select year, count(*) as key_count
    from by_key
    group by year
)

select year, sex, employment_type, age_group, 'duplicate' as check_name
from by_key
where row_count > 1
union all
select year, null, null, null, 'missing key' as check_name
from by_year
where key_count <> 42
