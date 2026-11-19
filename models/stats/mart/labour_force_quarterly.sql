-- 東京の労働力（労働力調査の東京都分）四半期平均の第1表（1行 = 年 × 四半期 × 分類 × 区分 × 男女）
select
    year,
    quarter,
    category,
    item,
    sex,
    unit,
    value,
    previous_year_value,
    change,
    change_rate
from {{ ref('stg_labour_force_quarterly') }}
order by year, quarter, category, item, sex
