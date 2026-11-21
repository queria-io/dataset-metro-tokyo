{# 東京の労働力（年平均の第3表）のステージング。
   区分から単位（千人・%）を決め、値を小数1桁の DECIMAL に型変換する（空欄は NULL）。
   同じ年の値は複数の年の表に載り、基準人口を切り替えた年の表（2012・2017・2022年）は
   前年（2011・2016・2021年）の値を新しい基準で計算し直している。年ごとに、値のある表の
   うち最も新しい年の表の値を使う。 #}

with source as (
    select
        cast(report_year as integer) as report_year,
        cast(year as integer) as year,
        sex,
        age_group,
        item,
        case
            when item in ('労働力人口比率', '就業率', '完全失業率') then '%'
            else '千人'
        end as unit,
        try_cast(nullif(trim(value), '') as decimal(8, 1)) as value
    from {{ ref('raw_labour_force_by_age') }}
)

select
    year,
    sex,
    age_group,
    item,
    unit,
    value,
    report_year
from source
where value is not null
qualify row_number() over (
    partition by year, sex, age_group, item order by report_year desc
) = 1
