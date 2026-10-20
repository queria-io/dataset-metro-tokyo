{# 毎月勤労統計調査（常用労働者数・パートタイム労働者比率）のステージング。
   労働者数を INTEGER、パートタイム労働者比率を DECIMAL に型変換し
   （原典の「×」「x」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直し、産業を符号と名前に分ける。
   産業名の揺れのそろえ方は stg_labour_earnings と同じ。 #}

{% set counts = [
    'employees_start', 'employees_start_male', 'employees_start_female',
    'employees_added', 'employees_added_male', 'employees_added_female',
    'employees_removed', 'employees_removed_male', 'employees_removed_female',
    'employees', 'employees_male', 'employees_female',
] %}
{% set ratios = ['part_time_ratio', 'part_time_ratio_male', 'part_time_ratio_female'] %}

select
    cast(year as integer) as year,
    case when period = '年平均' then '年平均' else '月次' end as period_type,
    case
        when period = '年平均' then null
        else cast(regexp_extract(period, '^(\d+)月$', 1) as integer)
    end as month,
    establishment_size,
    split_part(industry, ' ', 1) as industry_code,
    replace(
        regexp_replace(substr(industry, length(split_part(industry, ' ', 1)) + 2), '（注[0-9０-９]+）$', ''),
        '，', ','
    ) as industry_name,
    {%- for m in counts %}
    {{ stats_integer(m) }} as {{ m }},
    {%- endfor %}
    {%- for m in ratios %}
    {{ stats_decimal(m) }} as {{ m }}{{ "," if not loop.last }}
    {%- endfor %}
from {{ ref('raw_labour_employment') }}
