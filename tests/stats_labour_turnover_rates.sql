{# 入職率・離職率が、labour_employment の常用労働者数から計算した値と一致することを確かめる。
   原典では 入職率 = 増加労働者数 ÷ 前月末労働者数 × 100、離職率 = 減少労働者数 ÷ 前月末労働者数 × 100 を
   小数 2 桁に丸めた値で、月次の行で一致する。産業符号は産業名から引いて付けているので、
   引き当てを誤ると別の産業の労働者数と比べることになり、ここで見つかる。
   年平均の行は各月の率の平均なので、労働者数の年平均からの計算とは一致しない（比べない）。
   2018 年 7 月の 30 人以上の鉱業の離職率は、原典の第 12 表と第 10 表で食い違う（1.90 と 3.06）ので除く。
   秘匿で NULL の項を含む行は比べない。 #}

select
    t.year,
    t.month,
    t.establishment_size,
    t.industry_code,
    t.hiring_rate,
    t.separation_rate,
    e.employees_start,
    e.employees_added,
    e.employees_removed
from {{ ref('labour_turnover') }} as t
inner join {{ ref('labour_employment') }} as e
    on t.year = e.year
    and t.month = e.month
    and t.establishment_size = e.establishment_size
    and t.industry_code = e.industry_code
where t.period_type = '月次'
    and (
        t.hiring_rate <> round(e.employees_added * 100.0 / e.employees_start, 2)
        or (
            t.separation_rate <> round(e.employees_removed * 100.0 / e.employees_start, 2)
            and not (
                t.year = 2018 and t.month = 7
                and t.establishment_size = '30人以上' and t.industry_code = 'C'
            )
        )
    )
