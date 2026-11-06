{# 毎月勤労統計調査（規模・就業形態別月間出勤日数・実労働時間）のステージング。
   日数・時間を DECIMAL に型変換し（原典の「×」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直す。事業所規模の範囲の記号は「〜」にそろえる。 #}

{% set measures = [
    'general_days_worked', 'general_total_hours', 'general_scheduled_hours', 'general_overtime_hours',
    'part_time_days_worked', 'part_time_total_hours', 'part_time_scheduled_hours', 'part_time_overtime_hours',
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
    {{ stats_decimal(m) }} as {{ m }}{{ "," if not loop.last }}
    {%- endfor %}
from {{ ref('raw_labour_hours_by_size_and_employment_type') }}
