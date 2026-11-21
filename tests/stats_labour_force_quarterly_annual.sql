{# 千人単位の区分で、4つの四半期の平均が labour_force（年平均の第1表）の値と一致することを確かめる。
   年平均は各月の平均なので四半期の平均と同じになるはずで、千人単位の丸めの分だけ差が出る（差 1 まで許す）。
   率の区分は、年齢階級別の完全失業率で四半期の率の平均と年平均の率が最大 0.25 ずれるので比べない。 #}

with quarterly_mean as (
    select year, category, item, sex, avg(value) as mean_value
    from {{ ref('labour_force_quarterly') }}
    where unit = '千人'
    group by all
    having count(value) = 4
)

select q.year, q.category, q.item, q.sex, q.mean_value, a.value
from quarterly_mean as q
inner join {{ ref('labour_force') }} as a using (year, category, item, sex)
where abs(q.mean_value - a.value) > 1
