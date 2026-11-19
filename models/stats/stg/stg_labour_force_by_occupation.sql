{# 東京の労働力（年平均の第6表）のステージング。
   職業の「その他(左記以外のもの)」は「その他」にし、値（千人）を INTEGER に型変換する。
   同じ年の値は複数の年の表に載り、基準人口を切り替えた年の表（2012・2017・2022年）は
   前年（2011・2016・2021年）の値を新しい基準で計算し直している。年ごとに、値のある表の
   うち最も新しい年の表の値を使う。 #}

with source as (
    select
        cast(report_year as integer) as report_year,
        cast(year as integer) as year,
        sex,
        case
            when occupation = 'その他(左記以外のもの)' then 'その他'
            else occupation
        end as occupation,
        try_cast(nullif(trim(value), '') as integer) as value
    from {{ ref('raw_labour_force_by_occupation') }}
)

select
    year,
    sex,
    occupation,
    value,
    report_year
from source
where value is not null
qualify row_number() over (partition by year, sex, occupation order by report_year desc) = 1
