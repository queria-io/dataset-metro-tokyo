{# 東京の労働力（年平均の参考表）のステージング。
   同じ年の値は複数の年の表に載り、後の年の表で改訂されたものがある（2011年・2016年の一部）ので、
   年ごとに最も新しい年の表の値を使う。2011年の表では全国の値が「…」（岩手県、宮城県及び
   福島県を除く値だけが載る）だが、2012年からの表には全国の値が載る。
   値は小数1桁の DECIMAL に型変換し、「…」と空欄は NULL。 #}

with source as (
    select
        cast(report_year as integer) as report_year,
        cast(year as integer) as year,
        area,
        sex,
        try_cast(nullif(value, '') as decimal(4, 1)) as unemployment_rate
    from {{ ref('raw_labour_force_unemployment_rate') }}
)

select
    year,
    area,
    sex,
    unemployment_rate,
    report_year
from source
qualify row_number() over (partition by year, area, sex order by report_year desc) = 1
