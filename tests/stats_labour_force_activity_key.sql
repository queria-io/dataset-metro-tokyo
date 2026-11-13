{# 1行 = 年 × 男女 × 区分であること、各年・区分に男女計・男・女の3行がそろうこと、
   全期間にある区分（15歳以上人口・労働力人口・完全失業率など18区分）が毎年そろうことを確かめる。 #}

with by_key as (
    select year, sex, item, count(*) as row_count
    from {{ ref('labour_force_activity') }}
    group by all
),

by_item as (
    select year, item, count(*) as sex_count
    from by_key
    group by all
),

by_year as (
    select year, count(*) filter (where item not in (
        '就業率',
        '15歳以上人口／労働力人口／就業者数／雇用者数／うち常雇',
        '15歳以上人口／労働力人口／就業者数／雇用者数／うち正規の職員・従業員',
        '15歳以上人口／労働力人口／就業者数／雇用者数／うち非正規の職員・従業員',
        '15歳以上人口／労働力人口／就業者数／雇用者数／うち非正規の職員・従業員／うちパート・アルバイト'
    )) as item_count
    from by_item
    group by year
)

select year, sex, item, 'duplicate' as check_name
from by_key
where row_count > 1
union all
select year, null, item, 'missing sex' as check_name
from by_item
where sex_count <> 3
union all
select year, null, null, 'missing item' as check_name
from by_year
where item_count <> 18
