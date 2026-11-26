{# 東京の労働力（四半期平均の第2表）のステージング。
   区分の見出しの末尾の「（千人）」「（％、ポイント）」を単位の列（unit）に移し、
   全角の数字を半角にする。2003年7〜9月期の表だけは見出しが「労働力人口／総数」
   「労働力人口／就業者」「労働力人口／完全失業者」「非労働力人口」なので、後の表の
   「15歳以上人口／労働力人口」「…／就業者数」「…／完全失業者数」「15歳以上人口／非労働力人口」に
   そろえる。値は小数1桁の DECIMAL に型変換し、原典の「…」（該当なし）・「-」「－」（その表で
   調べていない区分）と空欄は NULL。
   同じ四半期の値は複数の表に載り、基準人口を切り替えた表（2012年1〜3月期・2017年1〜3月期・
   2022年1〜3月期）は直前の4〜5四半期の値を新しい基準で計算し直している。四半期ごとに、
   値のあるうち最も新しい表の値を使う。どの表にも値の無い区分の行は残さない。 #}

with source as (
    select
        cast(report_year as integer) as report_year,
        cast(report_quarter as integer) as report_quarter,
        cast(year as integer) as year,
        cast(quarter as integer) as quarter,
        sex,
        case regexp_replace(item, '（(千人|％、ポイント)）$', '')
            when '労働力人口／総数' then '15歳以上人口／労働力人口'
            when '労働力人口／就業者' then '15歳以上人口／労働力人口／就業者数'
            when '労働力人口／完全失業者' then '15歳以上人口／労働力人口／完全失業者数'
            when '非労働力人口' then '15歳以上人口／非労働力人口'
            else translate(
                regexp_replace(item, '（(千人|％、ポイント)）$', ''),
                '０１２３４５６７８９',
                '0123456789'
            )
        end as item,
        case when item like '%（千人）' then '千人' else '%' end as unit,
        try_cast(nullif(trim(value), '') as decimal(8, 1)) as value
    from {{ ref('raw_labour_force_activity_quarterly') }}
)

select
    year,
    quarter,
    sex,
    item,
    unit,
    value,
    report_year,
    report_quarter
from source
where value is not null
qualify row_number() over (
    partition by year, quarter, sex, item
    order by report_year desc, report_quarter desc
) = 1
