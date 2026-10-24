-- 毎月勤労統計調査（東京都）の規模別月間現金給与額（1行 = 年 × 月または年平均 × 事業所規模。調査産業計）
select
    year,
    period_type,
    month,
    establishment_size,
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
from {{ ref('stg_labour_earnings_by_size') }}
order by
    year,
    month nulls last,
    case establishment_size
        when '5〜29人' then 1
        when '30〜99人' then 2
        when '100〜499人' then 3
        when '500人以上' then 4
    end
