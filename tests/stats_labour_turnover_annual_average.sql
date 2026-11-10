{# 年平均の入職率・離職率が、その年の各月の率の平均と一致することを確かめる。
   原典の年平均は各月の率の平均を小数 2 桁に丸めた値で、12 か月そろう行で丸めの差 0.01 以内に収まる。
   列の割り当てがずれると値は数値のまま入るので、型や NULL の検査では見つからない。 #}

with monthly as (
    select
        year,
        establishment_size,
        industry_code,
        avg(hiring_rate) as hiring_rate,
        avg(separation_rate) as separation_rate,
        count(hiring_rate) as hiring_months,
        count(separation_rate) as separation_months
    from {{ ref('labour_turnover') }}
    where period_type = '月次'
    group by all
)

select
    a.year,
    a.establishment_size,
    a.industry_code,
    a.hiring_rate,
    m.hiring_rate as monthly_hiring_rate,
    a.separation_rate,
    m.separation_rate as monthly_separation_rate
from {{ ref('labour_turnover') }} as a
inner join monthly as m
    on a.year = m.year
    and a.establishment_size = m.establishment_size
    and a.industry_code = m.industry_code
where a.period_type = '年平均'
    and (
        (m.hiring_months = 12 and abs(a.hiring_rate - m.hiring_rate) > 0.011)
        or (m.separation_months = 12 and abs(a.separation_rate - m.separation_rate) > 0.011)
    )
