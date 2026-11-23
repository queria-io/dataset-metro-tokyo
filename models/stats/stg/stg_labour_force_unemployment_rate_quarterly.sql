{# 東京の労働力（四半期平均の参考表）のステージング。
   同じ四半期の値は複数の表に載り、後の表で改訂されたものがあるので、
   四半期ごとに最も新しい表（report_year、report_quarter の大きい方）の値を使う。
   2011年の表では全国の値が「…」（岩手県、宮城県及び福島県を除く値だけが載る）だが、
   後の表には全国の値が載る。
   値は小数1桁の DECIMAL に型変換し、「…」と空欄は NULL。 #}

with source as (
    select
        cast(report_year as integer) as report_year,
        cast(report_quarter as integer) as report_quarter,
        cast(year as integer) as year,
        cast(quarter as integer) as quarter,
        area,
        sex,
        try_cast(nullif(value, '') as decimal(4, 1)) as unemployment_rate
    from {{ ref('raw_labour_force_unemployment_rate_quarterly') }}
)

select
    year,
    quarter,
    area,
    sex,
    unemployment_rate,
    report_year,
    report_quarter
from source
qualify row_number() over (
    partition by year, quarter, area, sex
    order by report_year desc, report_quarter desc
) = 1
