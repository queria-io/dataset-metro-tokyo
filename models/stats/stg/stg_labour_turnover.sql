{# 毎月勤労統計調査（労働異動率）のステージング。
   入職率・離職率を小数2桁の DECIMAL に型変換し（原典の「×」「x」「ｘ」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直し、産業を符号と名前に分ける。
   産業名の揺れのそろえ方は stg_labour_earnings と同じ。 #}

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
    {{ stats_decimal('hiring_rate', 2) }} as hiring_rate,
    {{ stats_decimal('separation_rate', 2) }} as separation_rate
from {{ ref('raw_labour_turnover') }}
