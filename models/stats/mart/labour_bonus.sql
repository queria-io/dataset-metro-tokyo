-- 毎月勤労統計調査（東京都）の夏季・冬季賞与（1行 = 年 × 事業所規模 × 産業）
select
    year,
    establishment_size,
    industry_code,
    industry_name,
    summer_bonus,
    summer_bonus_change_rate,
    summer_paying_establishment_ratio,
    summer_receiving_employee_ratio,
    summer_bonus_months,
    summer_bonus_months_change,
    winter_bonus,
    winter_bonus_change_rate,
    winter_paying_establishment_ratio,
    winter_receiving_employee_ratio,
    winter_bonus_months,
    winter_bonus_months_change
from {{ ref('stg_labour_bonus') }}
order by year, establishment_size, industry_code
