-- 毎月勤労統計調査（東京都）の入職率・離職率（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    hiring_rate,
    separation_rate
from {{ ref('stg_labour_turnover') }}
order by year, month nulls last, establishment_size, industry_code
