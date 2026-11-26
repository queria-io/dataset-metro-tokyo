{# 千人単位の区分で、男女計が男と女の和と一致すること、労働力人口が就業者数と完全失業者数の和と
   一致することを、原典が千人単位に丸めている分の差 1 まで許して確かめる。
   労働力人口比率と就業率は、人数から計算して小数第1位に丸めた値と一致すること、
   完全失業率は、完全失業者数と労働力人口から計算した値との差が 0.1 ポイント以内であることを確かめる
   （2003年1〜3月期の男は 174 ÷ 4,000 = 4.35 を原典が 4.4 としており、丸めた人数から
   計算した値は 4.3 になる）。
   15歳以上人口は就業状態不詳を含むので、労働力人口と非労働力人口の和とは比べない。 #}

with by_sex as (
    pivot (
        select year, quarter, item, sex, value
        from {{ ref('labour_force_activity_quarterly') }}
        where unit = '千人'
    )
    on sex using first(value)
),

sex_mismatch as (
    select year, quarter, item, '男女計 <> 男 + 女' as check_name
    from by_sex
    where abs("男女計" - "男" - "女") > 1
),

by_item as (
    pivot (
        select year, quarter, sex, item, value
        from {{ ref('labour_force_activity_quarterly') }}
    )
    on item using first(value)
)

select * from sex_mismatch
union all
select year, quarter, sex, '労働力人口 <> 就業者数 + 完全失業者数'
from by_item
where abs(
    "15歳以上人口／労働力人口"
    - "15歳以上人口／労働力人口／就業者数"
    - "15歳以上人口／労働力人口／完全失業者数"
) > 1
union all
select year, quarter, sex, '完全失業率 <> 完全失業者数 / 労働力人口'
from by_item
where abs(
    "15歳以上人口／労働力人口／完全失業者数" / "15歳以上人口／労働力人口" * 100 - "完全失業率"
) > 0.1
union all
select year, quarter, sex, '労働力人口比率 <> 労働力人口 / 15歳以上人口'
from by_item
where round("15歳以上人口／労働力人口" / "15歳以上人口" * 100, 1) <> "労働力人口比率"
union all
select year, quarter, sex, '就業率 <> 就業者数 / 15歳以上人口'
from by_item
where "就業率" is not null
    and round("15歳以上人口／労働力人口／就業者数" / "15歳以上人口" * 100, 1) <> "就業率"
