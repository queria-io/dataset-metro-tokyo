{# 東京の労働力（年平均の第2表）のステージング。
   区分の見出しの末尾の「（千人）」「（％、ポイント）」を単位の列（unit）に移す。
   「うち常雇（再掲）」（2013〜2017年の表）は他の年の表の「うち常雇」にそろえ、
   半角の中点「･」は全角の「・」にする。
   値は小数1桁の DECIMAL に型変換し、原典の「…」（該当なし）・「-」「－」（その年の表で
   調べていない区分）と空欄は NULL。
   同じ年の値は複数の年の表に載り、基準人口を切り替えた年の表（2012・2017・2022年）は
   前年（2011・2016・2021年）の値を新しい基準で計算し直している。年ごとに、値のある表の
   うち最も新しい年の表の値を使う。どの表にも値の無い区分の行は残さない。 #}

with source as (
    select
        cast(report_year as integer) as report_year,
        cast(year as integer) as year,
        sex,
        replace(
            replace(regexp_replace(item, '（(千人|％、ポイント)）$', ''), '（再掲）', ''),
            '･', '・'
        ) as item,
        case when item like '%（千人）' then '千人' else '%' end as unit,
        try_cast(nullif(trim(value), '') as decimal(8, 1)) as value
    from {{ ref('raw_labour_force_activity') }}
)

select
    year,
    sex,
    item,
    unit,
    value,
    report_year
from source
where value is not null
qualify row_number() over (partition by year, sex, item order by report_year desc) = 1
