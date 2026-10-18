-- 毎月勤労統計調査（東京都）の月間現金給与額（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    cash_earnings,
    cash_earnings_male,
    cash_earnings_female,
    contractual_earnings,
    contractual_earnings_male,
    contractual_earnings_female,
    scheduled_earnings,
    overtime_earnings,
    special_earnings,
    special_earnings_male,
    special_earnings_female
from {{ ref('stg_labour_earnings') }}
order by year, month nulls last, establishment_size, industry_code
