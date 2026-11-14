{# 千人単位の区分で、男女計が男と女の和と、年齢階級の総数が各年齢階級の和と一致すること、
   労働力人口が就業者数と完全失業者数の和と一致すること、労働力人口比率・就業率・完全失業率が
   人数から計算した値と一致することを確かめる。原典は千人単位に丸めているので、人数の差は
   男女で 1 まで、年齢階級（6区分）で 3 まで許す。
   原典の 1997年の15歳以上人口（総数）は男女計 10311 に対して男と女の和が 10309 なので除く。
   15歳以上人口は就業状態不詳を含むので、労働力人口と非労働力人口の和とは比べない。 #}

with persons as (
    select year, sex, age_group, item, value
    from {{ ref('labour_force_by_age') }}
    where unit = '千人'
),

by_sex as (
    pivot (select year, age_group, item, sex, value from persons)
    on sex using first(value)
),

sex_mismatch as (
    select year, age_group as key, item, '男女計 <> 男 + 女' as check_name
    from by_sex
    where abs("男女計" - "男" - "女") > 1
        and not (year = 1997 and age_group = '総数' and item = '15歳以上人口')
),

age_mismatch as (
    select year, sex as key, item, '総数 <> 年齢階級の和' as check_name
    from persons
    group by year, sex, item
    having abs(
        sum(value) filter (where age_group = '総数')
        - sum(value) filter (where age_group <> '総数')
    ) > 3
        or count(*) filter (where age_group = '総数') <> 1
),

by_item as (
    pivot (
        select year, sex, age_group, item, value
        from {{ ref('labour_force_by_age') }}
    )
    on item using first(value)
),

item_mismatch as (
    select year, sex || '／' || age_group as key, null as item,
        '労働力人口 <> 就業者数 + 完全失業者数' as check_name
    from by_item
    where abs("労働力人口" - "就業者数" - "完全失業者数") > 1
    union all
    select year, sex || '／' || age_group, null, '完全失業率 <> 完全失業者数 / 労働力人口'
    from by_item
    where round("完全失業者数" / "労働力人口" * 100, 1) <> "完全失業率"
    union all
    select year, sex || '／' || age_group, null, '労働力人口比率 <> 労働力人口 / 15歳以上人口'
    from by_item
    where round("労働力人口" / "15歳以上人口" * 100, 1) <> "労働力人口比率"
    union all
    select year, sex || '／' || age_group, null, '就業率 <> 就業者数 / 15歳以上人口'
    from by_item
    where round("就業者数" / "15歳以上人口" * 100, 1) <> "就業率"
)

select * from sex_mismatch
union all
select * from age_mismatch
union all
select * from item_mismatch
