{# 千人単位の区分で、男女計が男と女の和と一致すること、労働力人口が就業者数と完全失業者数の和と
   一致することを確かめる。原典は千人単位に丸めているので、差は 1 まで許す。
   2003年7〜9月期〜2004年1〜3月期の見出しを後の表の形にそろえられていないと、
   就業者数と完全失業者数の列が空になってこの検査から漏れるので、空も失敗にする。 #}

with by_sex as (
    pivot (
        select year, quarter, category, item, sex, value
        from {{ ref('labour_force_quarterly') }}
        where unit = '千人'
    )
    on sex using first(value)
),

by_item as (
    pivot (
        select year, quarter, sex, item, value
        from {{ ref('labour_force_quarterly') }}
        where category = '就業状態'
    )
    on item using first(value)
)

select year, quarter, category, item, '男女計 <> 男 + 女' as check_name
from by_sex
where abs("男女計" - "男" - "女") > 1
union all
select year, quarter, '就業状態', sex, '労働力人口 <> 就業者数 + 完全失業者数'
from by_item
where abs("労働力人口" - "労働力人口／就業者数" - "労働力人口／完全失業者数") > 1
    or "労働力人口／就業者数" is null
    or "労働力人口／完全失業者数" is null
