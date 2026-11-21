-- 東京の労働力 年平均の第3表（1行 = 年 × 男女 × 年齢階級 × 区分）。年齢階級別の15歳以上人口・労働力人口・就業者数・完全失業者数・非労働力人口と、労働力人口比率・就業率・完全失業率
select
    year,
    sex,
    age_group,
    item,
    unit,
    value,
    report_year
from {{ ref('stg_labour_force_by_age') }}
order by year, sex, age_group, item
