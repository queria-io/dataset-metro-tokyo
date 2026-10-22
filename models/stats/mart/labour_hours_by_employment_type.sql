-- 毎月勤労統計調査（東京都）の就業形態別月間出勤日数・実労働時間（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    general_days_worked,
    general_total_hours,
    general_scheduled_hours,
    general_overtime_hours,
    part_time_days_worked,
    part_time_total_hours,
    part_time_scheduled_hours,
    part_time_overtime_hours
from {{ ref('stg_labour_hours_by_employment_type') }}
order by year, month nulls last, establishment_size, industry_code
