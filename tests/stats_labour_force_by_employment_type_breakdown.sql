{# 総数が labour_force の正規・非正規の職員・従業員数と一致すること、年齢階級の和が総数と、
   男女計が男と女の和と一致することを確かめる。
   基準人口を切り替えた年の前年（2016・2021年）は、この表は新しい基準で計算し直した値を
   持つので、labour_force の翌年の行の前年の値（previous_year_value）と比べる。
   原典は千人単位に丸めているので、年齢階級の和は差 2 まで、男女の和は差 1 まで許す。 #}

with total as (
    select year, sex, employment_type, value
    from {{ ref('labour_force_by_employment_type') }}
    where age_group = '総数'
),

age_sum as (
    select year, sex, employment_type, sum(value) as value
    from {{ ref('labour_force_by_employment_type') }}
    where age_group <> '総数'
    group by all
),

employees as (
    select
        year,
        sex,
        case
            when item like '%うち正規の職員・従業員' then '正規'
            else '非正規'
        end as employment_type,
        value,
        previous_year_value
    from {{ ref('labour_force') }}
    where category = '就業状態'
        and (
            item like '%雇用者数／うち正規の職員・従業員'
            or item like '%雇用者数／うち非正規の職員・従業員'
        )
),

by_sex as (
    pivot (
        select year, employment_type, age_group, sex, value
        from {{ ref('labour_force_by_employment_type') }}
    )
    on sex using first(value)
)

select t.year, t.sex || '／' || t.employment_type as key, '総数 <> labour_force' as check_name
from total as t
left join employees as e using (year, sex, employment_type)
left join employees as next_year
    on next_year.year = t.year + 1
    and next_year.sex = t.sex
    and next_year.employment_type = t.employment_type
where t.value is distinct from (
    case when t.year in (2016, 2021) then next_year.previous_year_value else e.value end
)
union all
select t.year, t.sex || '／' || t.employment_type, '年齢階級の和 <> 総数'
from total as t
inner join age_sum as a using (year, sex, employment_type)
where abs(t.value - a.value) > 2
union all
select year, employment_type || '／' || age_group, '男女計 <> 男 + 女'
from by_sex
where abs("男女計" - "男" - "女") > 1
