{# 毎月勤労統計調査（規模・就業形態別月間現金給与額）のステージング。
   金額を INTEGER に型変換し（原典の「×」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直す。事業所規模の範囲の記号は「〜」にそろえる。 #}

{% set measures = [
    'general_cash_earnings', 'general_contractual_earnings', 'general_scheduled_earnings',
    'general_overtime_earnings', 'general_special_earnings',
    'part_time_cash_earnings', 'part_time_contractual_earnings', 'part_time_scheduled_earnings',
    'part_time_overtime_earnings', 'part_time_special_earnings',
] %}

select
    cast(year as integer) as year,
    case when period = '年平均' then '年平均' else '月次' end as period_type,
    case
        when period = '年平均' then null
        else cast(regexp_extract(period, '^(\d+)月$', 1) as integer)
    end as month,
    replace(establishment_size, '~', '〜') as establishment_size,
    {%- for m in measures %}
    {{ stats_integer(m) }} as {{ m }}{{ "," if not loop.last }}
    {%- endfor %}
from {{ ref('raw_labour_earnings_by_size_and_employment_type') }}
