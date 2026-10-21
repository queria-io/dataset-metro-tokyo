-- 毎月勤労統計調査（東京都）の就業形態別月間現金給与額（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    general_cash_earnings,
    general_contractual_earnings,
    general_scheduled_earnings,
    general_overtime_earnings,
    general_special_earnings,
    part_time_cash_earnings,
    part_time_contractual_earnings,
    part_time_scheduled_earnings,
    part_time_overtime_earnings,
    part_time_special_earnings
from {{ ref('stg_labour_earnings_by_employment_type') }}
order by year, month nulls last, establishment_size, industry_code
