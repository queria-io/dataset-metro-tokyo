{# 毎月勤労統計調査（規模別月間現金給与額）のステージング。
   金額を INTEGER に型変換し（原典の「×」（秘匿）と「－」（該当なし）は NULL）、
   「年平均・月」を月の番号に直す。事業所規模の範囲の記号は「〜」にそろえる。 #}

{% set measures = [
    'cash_earnings', 'cash_earnings_male', 'cash_earnings_female',
    'contractual_earnings', 'contractual_earnings_male', 'contractual_earnings_female',
    'scheduled_earnings', 'overtime_earnings',
    'special_earnings', 'special_earnings_male', 'special_earnings_female',
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
from {{ ref('raw_labour_earnings_by_size') }}
