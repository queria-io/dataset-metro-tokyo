-- 東京の労働力 四半期平均の参考表（1行 = 四半期 × 地域 × 男女）。東京都・南関東・全国の完全失業率
select
    year,
    quarter,
    area,
    sex,
    unemployment_rate,
    report_year,
    report_quarter
from {{ ref('stg_labour_force_unemployment_rate_quarterly') }}
order by year, quarter, area, sex
