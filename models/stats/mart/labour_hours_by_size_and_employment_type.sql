-- 毎月勤労統計調査（東京都）の規模・就業形態別月間出勤日数・実労働時間（1行 = 年 × 月または年平均 × 事業所規模。調査産業計）
select
    year,
    period_type,
    month,
    establishment_size,
    general_days_worked,
    general_total_hours,
    general_scheduled_hours,
    general_overtime_hours,
    part_time_days_worked,
    part_time_total_hours,
    part_time_scheduled_hours,
    part_time_overtime_hours
from {{ ref('stg_labour_hours_by_size_and_employment_type') }}
order by
    year,
    month nulls last,
    case establishment_size
        when '5〜29人' then 1
        when '30〜99人' then 2
        when '100〜499人' then 3
        when '500人以上' then 4
    end
