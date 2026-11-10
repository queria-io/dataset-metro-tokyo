{# 毎月勤労統計調査（規模、産業別の指数）のステージング。
   指数と前年比・前年同月比を小数1桁の DECIMAL に型変換し（原典の「×」「x」「ｘ」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直し、産業を符号と名前に分ける。
   産業名の揺れのそろえ方は stg_labour_turnover と同じ。 #}

select
    index_type,
    cast(base_year as integer) as base_year,
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
    {{ stats_decimal('index_value', 1) }} as index_value,
    {{ stats_decimal('change_rate', 1) }} as change_rate
from {{ ref('raw_labour_index') }}
