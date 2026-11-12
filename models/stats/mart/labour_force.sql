-- 東京の労働力（労働力調査の東京都分）年平均の第1表（1行 = 年 × 分類 × 区分 × 男女）
select
    year,
    category,
    item,
    sex,
    unit,
    value,
    previous_year_value,
    change,
    change_rate
from {{ ref('stg_labour_force') }}
order by year, category, item, sex
