{# 7職業の和が labour_force の就業者数（男女別）と、男女計が男と女の和と一致することを確かめる。
   基準人口を切り替えた年の前年（2011・2016・2021年）は、この表は新しい基準で計算し直した値を
   持つので、labour_force の翌年の行の前年の値（previous_year_value）と比べる。
   原典は千人単位に丸めているので、職業の和は差 2 まで、男女の和は差 1 まで許す
   （「その他」だけは男女の和との差が 3 の年があるので 3 まで許す）。 #}

with occupation_total as (
    select year, sex, sum(value) as total
    from {{ ref('labour_force_by_occupation') }}
    group by all
),

employed as (
    select year, sex, value, previous_year_value
    from {{ ref('labour_force') }}
    where category = '就業状態' and item = '労働力人口／就業者数'
),

by_sex as (
    pivot (
        select year, occupation, sex, value
        from {{ ref('labour_force_by_occupation') }}
    )
    on sex using first(value)
)

select o.year, o.sex as key, '職業の和 <> 就業者数' as check_name
from occupation_total as o
inner join employed as e using (year, sex)
left join employed as next_year
    on next_year.year = o.year + 1 and next_year.sex = o.sex
where abs(
    o.total
    - case when o.year in (2011, 2016, 2021) then next_year.previous_year_value else e.value end
) > 2
union all
select year, occupation, '男女計 <> 男 + 女'
from by_sex
where abs("男女計" - "男" - "女") > case when occupation = 'その他' then 3 else 1 end
