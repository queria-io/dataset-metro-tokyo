-- 東京の労働力 年平均の第6表（1行 = 年 × 男女 × 職業）。主な職業別の就業者数（千人）
select
    year,
    sex,
    occupation,
    value,
    report_year
from {{ ref('stg_labour_force_by_occupation') }}
order by year, sex, occupation
