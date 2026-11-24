-- 都民のくらしむき 家計収支（全世帯）の長期時系列（1行 = 年 × 項目）
select
    year,
    item,
    unit,
    value,
    nominal_growth_rate,
    real_growth_rate
from {{ ref('stg_household_budget') }}
order by year, item
