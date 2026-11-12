-- 東京の労働力 年平均の参考表（1行 = 年 × 地域 × 男女）。東京都・南関東・全国の完全失業率
select
    year,
    area,
    sex,
    unemployment_rate,
    report_year
from {{ ref('stg_labour_force_unemployment_rate') }}
order by year, area, sex
