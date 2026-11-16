-- 東京の労働力 年平均の第8表（1行 = 年 × 男女 × 雇用形態 × 年齢階級）。役員を除く雇用者数（千人）
select
    year,
    sex,
    employment_type,
    age_group,
    value,
    report_year
from {{ ref('stg_labour_force_by_employment_type') }}
order by year, sex, employment_type, age_group
