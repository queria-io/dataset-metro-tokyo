{# 千人単位の区分で、男女計が男と女の和と一致すること、労働力人口が就業者数と完全失業者数の和と
   一致することを確かめる。原典は千人単位に丸めているので、差は 1 まで許す。
   2007年の「その他(上記以外のもの)」は原典で男女の和が合わない（就業者 358 に対して 236 + 120、
   雇用者 314 に対して 193 + 98）ので除く。2008年の表の前年の値では合う形に直っている。
   15歳以上人口は就業状態不詳を含むので、労働力人口と非労働力人口の和とは比べない。 #}

with by_sex as (
    pivot (
        select year, category, item, sex, value
        from {{ ref('labour_force') }}
        where unit = '千人'
    )
    on sex using first(value)
),

sex_mismatch as (
    select year, category, item, '男女計 <> 男 + 女' as check_name
    from by_sex
    where abs("男女計" - "男" - "女") > 1
        and not (year = 2007 and item = 'その他(上記以外のもの)')
),

by_item as (
    pivot (
        select year, sex, item, value
        from {{ ref('labour_force') }}
        where category = '就業状態'
    )
    on item using first(value)
),

labour_force_mismatch as (
    select year, '就業状態' as category, sex as item, '労働力人口 <> 就業者数 + 完全失業者数' as check_name
    from by_item
    where abs("労働力人口" - "労働力人口／就業者数" - "労働力人口／完全失業者数") > 1
)

select * from sex_mismatch
union all
select * from labour_force_mismatch
