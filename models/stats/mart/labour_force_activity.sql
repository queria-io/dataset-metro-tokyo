-- 東京の労働力 年平均の第2表（1行 = 年 × 男女 × 区分）。就業状態・活動状態・従業上の地位別の15歳以上人口と、労働力人口比率・就業率・完全失業率
select
    year,
    sex,
    item,
    unit,
    value,
    report_year
from {{ ref('stg_labour_force_activity') }}
order by year, sex, item
