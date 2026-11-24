{# 1行 = 年 × 項目であること、各年に72項目がそろうこと、
   1975〜2025年の51年が欠けないこと、エンゲル係数が生計支出／消費支出／食料 ÷ 消費支出（％）と
   0.1ポイント以内で一致することを確かめる。 #}

with by_key as (
    select year, item, count(*) as row_count
    from {{ ref('household_budget') }}
    group by all
),

by_year as (
    select year, count(*) as item_count
    from by_key
    group by year
),

engel as (
    select
        e.year,
        e.value as reported,
        f.value / k.value * 100 as computed
    from {{ ref('household_budget') }} as e
    inner join {{ ref('household_budget') }} as f
        on e.year = f.year and f.item = '生計支出／消費支出／食料'
    inner join {{ ref('household_budget') }} as k
        on e.year = k.year and k.item = '生計支出／消費支出'
    where e.item = 'エンゲル係数'
)

select year, item, 'duplicate' as check_name
from by_key
where row_count > 1
union all
select year, null, 'item count is not 72' as check_name
from by_year
where item_count <> 72
union all
select null, null, 'years are not 1975-2025' as check_name
from (select min(year) as first_year, max(year) as last_year, count(distinct year) as years from by_year)
where first_year <> 1975 or last_year - first_year + 1 <> years
union all
select year, 'エンゲル係数', 'engel coefficient mismatch' as check_name
from engel
where abs(reported - computed) > 0.1
