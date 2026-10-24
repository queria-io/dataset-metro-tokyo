{# 毎月勤労統計調査（就業形態別常用労働者数）のステージング。
   労働者数を INTEGER に型変換し（原典の「×」「x」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直し、産業を符号と名前に分ける。
   産業名の揺れのそろえ方は stg_labour_earnings と同じ。
   2016年の第11-1表の鉱業は「年平均・月」が空欄で値もすべて「－」なので、その行は落とす。 #}

{% set counts = [
    'general_employees_start', 'general_employees_added', 'general_employees_removed', 'general_employees',
    'part_time_employees_start', 'part_time_employees_added', 'part_time_employees_removed', 'part_time_employees',
] %}

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
    {{ stats_integer(m) }} as {{ m }}{{ "," if not loop.last }}
    {%- endfor %}
from {{ ref('raw_labour_employment_by_employment_type') }}
where nullif(trim(period), '') is not null
