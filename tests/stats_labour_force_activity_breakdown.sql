{# 千人単位の区分で、男女計が男と女の和と一致すること、労働力人口が就業者数と完全失業者数の和と、
   非労働力人口が通学・家事・その他の和と一致すること、完全失業率が完全失業者数と労働力人口から
   計算した値と一致することを確かめる。原典は千人単位に丸めているので、人数の差は 1 まで許す。
   原典の 1997年の男女計の「非労働力人口／その他」は 922 で、男と女の和（992）とも
   非労働力人口からの差し引き（992）とも合わないので除く。
   15歳以上人口は就業状態不詳を含むので、労働力人口と非労働力人口の和とは比べない。 #}

with by_sex as (
    pivot (
        select year, item, sex, value
        from {{ ref('labour_force_activity') }}
        where unit = '千人'
    )
    on sex using first(value)
),

sex_mismatch as (
    select year, item, '男女計 <> 男 + 女' as check_name
    from by_sex
    where abs("男女計" - "男" - "女") > 1
        and not (year = 1997 and item = '15歳以上人口／非労働力人口／その他')
),

by_item as (
    pivot (
        select year, sex, item, value
        from {{ ref('labour_force_activity') }}
    )
    on item using first(value)
),

breakdown_mismatch as (
    select year, sex as item, '労働力人口 <> 就業者数 + 完全失業者数' as check_name
    from by_item
    where abs(
        "15歳以上人口／労働力人口"
        - "15歳以上人口／労働力人口／就業者数"
        - "15歳以上人口／労働力人口／完全失業者数"
    ) > 1
    union all
    select year, sex, '非労働力人口 <> 通学 + 家事 + その他'
    from by_item
    where abs(
        "15歳以上人口／非労働力人口"
        - "15歳以上人口／非労働力人口／通学"
        - "15歳以上人口／非労働力人口／家事"
        - "15歳以上人口／非労働力人口／その他"
    ) > 1
        and not (year = 1997 and sex = '男女計')
    union all
    select year, sex, '完全失業率 <> 完全失業者数 / 労働力人口'
    from by_item
    where round("15歳以上人口／労働力人口／完全失業者数" / "15歳以上人口／労働力人口" * 100, 1)
        <> "完全失業率"
)

select * from sex_mismatch
union all
select * from breakdown_mismatch
