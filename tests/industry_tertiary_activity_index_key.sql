{# 1行 = 月 × 指数の種類 × 品目番号であること、原指数と季節調整済指数の行数が同じであること、
   第3次産業総合の指数が全月で空でないことを確かめる。 #}

with by_key as (
    select year, month, index_type, item_code, count(*) as row_count
    from {{ ref('tertiary_activity_index') }}
    group by all
),

items as (
    select index_type, count(*) as row_count
    from {{ ref('tertiary_activity_index') }}
    group by index_type
)

select year, month, index_type, item_code, 'duplicate' as check_name
from by_key
where row_count > 1
union all
select null, null, null, null, 'row count differs between index types' as check_name
where (select count(distinct row_count) from items) > 1
union all
select year, month, index_type, item_code, 'total is null' as check_name
from {{ ref('tertiary_activity_index') }}
where item_code = 'K1D000000I' and index_value is null
