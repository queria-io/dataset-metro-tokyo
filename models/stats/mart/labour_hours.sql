-- 毎月勤労統計調査（東京都）の月間出勤日数・実労働時間（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    days_worked,
    days_worked_male,
    days_worked_female,
    total_hours,
    total_hours_male,
    total_hours_female,
    scheduled_hours,
    scheduled_hours_male,
    scheduled_hours_female,
    overtime_hours,
    overtime_hours_male,
    overtime_hours_female
from {{ ref('stg_labour_hours') }}
order by year, month nulls last, establishment_size, industry_code
