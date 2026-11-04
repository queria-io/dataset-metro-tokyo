-- 毎月勤労統計調査（東京都）の規模別月間出勤日数・実労働時間（1行 = 年 × 月または年平均 × 事業所規模。調査産業計）
select
    year,
    period_type,
    month,
    establishment_size,
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
from {{ ref('stg_labour_hours_by_size') }}
order by
    year,
    month nulls last,
    case establishment_size
        when '5〜29人' then 1
        when '30〜99人' then 2
        when '100〜499人' then 3
        when '500人以上' then 4
    end
