-- 東京の労働力 四半期平均の第2表（1行 = 四半期 × 男女 × 区分）。15歳以上人口の就業状態別の人数と、労働力人口比率・就業率・完全失業率
select
    year,
    quarter,
    sex,
    item,
    unit,
    value,
    report_year,
    report_quarter
from {{ ref('stg_labour_force_activity_quarterly') }}
order by year, quarter, sex, item
