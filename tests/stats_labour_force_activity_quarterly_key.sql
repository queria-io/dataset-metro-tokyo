{# 1行 = 四半期 × 男女 × 区分であること、各四半期・区分に男女計・男・女の3行がそろうこと、
   1997年1〜3月期から最新の四半期まで欠けが無いこと、就業率を除く7区分（15歳以上人口・
   労働力人口・就業者数・完全失業者数・非労働力人口・労働力人口比率・完全失業率）が
   毎四半期そろうこと、就業率が2011年7〜9月期から毎四半期そろうことを確かめる。 #}

with by_key as (
    select year, quarter, sex, item, count(*) as row_count
    from {{ ref('labour_force_activity_quarterly') }}
    group by all
),

by_item as (
    select year, quarter, item, count(*) as sex_count
    from by_key
    group by all
),

by_period as (
    select
        year,
        quarter,
        count(*) filter (where item <> '就業率') as item_count,
        count(*) filter (where item = '就業率') as employment_rate_count
    from by_item
    group by all
),

bounds as (
    select
        min(year * 4 + quarter) as first_period,
        max(year * 4 + quarter) as last_period,
        count(*) as period_count
    from by_period
)

select year, quarter, sex, item, 'duplicate or invalid quarter' as check_name
from by_key
where row_count > 1 or quarter not between 1 and 4
union all
select year, quarter, null, item, 'missing sex' as check_name
from by_item
where sex_count <> 3
union all
select year, quarter, null, null, 'missing item' as check_name
from by_period
where item_count <> 7
union all
select year, quarter, null, '就業率', 'missing employment rate' as check_name
from by_period
where year * 10 + quarter >= 20113 and employment_rate_count <> 1
union all
select null, null, null, null, 'period gap' as check_name
from bounds
where first_period <> 1997 * 4 + 1 or last_period - first_period + 1 <> period_count
