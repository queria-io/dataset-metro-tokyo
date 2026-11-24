{# 都民のくらしむき（長期時系列表1）のステージング。
   指標（実数・対前年名目増加率・対前年実質増加率）の行を、年 × 項目の1行に並べ直す。
   値は DECIMAL に型変換し、「-」（該当なし）と空欄は NULL。
   実数の単位は項目の見出しの末尾（円・人・世帯・歳・％）、増加率は％。 #}

with source as (
    select
        cast(year as integer) as year,
        measure,
        item_path as item,
        unit,
        try_cast(nullif(value, '') as decimal(12, 2)) as value
    from {{ ref('raw_household_budget') }}
)

select
    year,
    item,
    any_value(unit) as unit,
    max(value) filter (where measure = 'actual') as value,
    max(value) filter (where measure = 'nominal_growth') as nominal_growth_rate,
    max(value) filter (where measure = 'real_growth') as real_growth_rate
from source
group by year, item
