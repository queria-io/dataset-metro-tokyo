{# 年平均の指数が、その年の各月の指数の平均と一致することを確かめる。
   名目賃金・労働時間・常用雇用の指数は、各月の平均と丸めの差 0.1 以内に収まる。
   実質賃金指数の年平均は名目賃金指数の年平均を消費者物価指数の年平均で割った値なので、
   各月の平均とは最大 0.32 ずれる（差 0.4 まで許す）。12 か月そろう行だけを比べる。
   原典の 2013 年報の第15表では、30人以上の金融業,保険業（J）と学術研究,専門・技術サービス業（L）の
   年平均（98・103）が各月の平均（95.2・89.7）とも 2014 年報の 2013 年の年平均とも合わないので除く。
   指数の行と前年比の行の組み合わせを誤っても値は数値のまま入るので、型や NULL の検査では見つからない。 #}

with monthly as (
    select
        index_type,
        year,
        establishment_size,
        industry_code,
        avg(index_value) as index_value,
        count(index_value) as months
    from {{ ref('labour_index') }}
    where period_type = '月次'
    group by all
)

select
    a.index_type,
    a.year,
    a.establishment_size,
    a.industry_code,
    a.index_value,
    m.index_value as monthly_index_value
from {{ ref('labour_index') }} as a
inner join monthly as m
    on a.index_type = m.index_type
    and a.year = m.year
    and a.establishment_size = m.establishment_size
    and a.industry_code = m.industry_code
where a.period_type = '年平均'
    and m.months = 12
    and abs(a.index_value - m.index_value)
        > case when a.index_type like '実質賃金指数%' then 0.4 else 0.11 end
    and not (
        a.index_type = '名目賃金指数（所定内給与）'
        and a.year = 2013
        and a.establishment_size = '30人以上'
        and a.industry_code in ('J', 'L')
    )
