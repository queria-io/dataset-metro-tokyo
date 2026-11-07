{# 毎月勤労統計調査（夏季・冬季賞与）のステージング。
   支給額を INTEGER、割合・前年比を小数1桁、支給月数を小数2桁の DECIMAL に型変換し
   （原典の「×」「ｘ」（秘匿）と「－」（該当なし）は NULL）、産業を符号と名前に分ける。
   産業符号と名前の間の空白が無い行（2017年までの「PSＰ一括分」）があるため、符号は先頭の
   半角英数字と記号で切り出す。産業名は labour_earnings と同じく注記を落として読点を半角にそろえる。 #}

{% set seasons = ['summer', 'winter'] %}

select
    cast(year as integer) as year,
    establishment_size,
    regexp_extract(industry, '^([A-Z][A-Z0-9,\-]*)', 1) as industry_code,
    replace(
        regexp_replace(
            trim(substr(industry, length(regexp_extract(industry, '^([A-Z][A-Z0-9,\-]*)', 1)) + 1)),
            '（注[0-9０-９]+）$', ''
        ),
        '，', ','
    ) as industry_name,
    {%- for s in seasons %}
    {{ stats_integer(s ~ '_bonus') }} as {{ s }}_bonus,
    {{ stats_decimal(s ~ '_bonus_change_rate') }} as {{ s }}_bonus_change_rate,
    {{ stats_decimal(s ~ '_paying_establishment_ratio') }} as {{ s }}_paying_establishment_ratio,
    {{ stats_decimal(s ~ '_receiving_employee_ratio') }} as {{ s }}_receiving_employee_ratio,
    {{ stats_decimal(s ~ '_bonus_months', 2) }} as {{ s }}_bonus_months,
    {{ stats_decimal(s ~ '_bonus_months_change', 2) }} as {{ s }}_bonus_months_change{{ "," if not loop.last }}
    {%- endfor %}
from {{ ref('raw_labour_bonus') }}
