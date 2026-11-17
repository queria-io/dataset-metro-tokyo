{# 1行 = 年 × 四半期 × 分類 × 区分 × 男女であることと、実数が空でないことを確かめる。
   四半期は 1〜4。分類は区分の見出しの〔〕から切り出しているので、切り出しに失敗すると
   分類が空になるか、別の区分と重なる。
   2004年1〜3月期までの表の見出しは stg で後の表の形にそろえているので、その (分類, 区分) が
   2004年4〜6月期以降にも現れることも確かめる。そろえ漏れがあると、後の表に無い区分として残る。 #}

with by_key as (
    select
        year,
        quarter,
        category,
        item,
        sex,
        count(*) as row_count,
        count(value) as value_count
    from {{ ref('labour_force_quarterly') }}
    group by all
),

later_items as (
    select distinct category, item
    from {{ ref('labour_force_quarterly') }}
    where year * 10 + quarter > 20041
)

select year, quarter, category, item, sex, 'invalid key' as check_name
from by_key
where category = '' or item = '' or quarter not between 1 and 4
    or row_count > 1 or value_count < row_count
union all
select distinct year, quarter, category, item, null, 'item not in later tables'
from by_key
anti join later_items using (category, item)
where year * 10 + quarter <= 20041
