{# 東京都の完全失業率が、labour_force_quarterly（その四半期の表の第1表）の完全失業率の総数と一致することを確かめる。
   参考表は最も新しい表の値を使うので、後の表で改訂された四半期は一致しない。
   原典で食い違うのは次の13件だけ（基準人口を切り替えた年の表が前の期間を計算し直したもの）。
   2011年1期の男女計・女、2期の男女計・男、3期の男女計、4期の男、2015年4期の男、
   2016年2期の男女計、4期の男、2021年1期の男、2期の男・女、3期の女。
   分類名が変わって結合が0件になったときも、比べた四半期が足りないものとして落とす。 #}

with rate as (
    select year, quarter, sex, unemployment_rate
    from {{ ref('labour_force_unemployment_rate_quarterly') }}
    where area = '東京都'
),

first_table as (
    select year, quarter, sex, value
    from {{ ref('labour_force_quarterly') }}
    where category = '完全失業率（年齢階級別）'
        and item = '総数'
),

compared as (
    select rate.year, rate.quarter, rate.sex, rate.unemployment_rate, first_table.value
    from rate
    inner join first_table using (year, quarter, sex)
)

select year, quarter, sex, unemployment_rate, value
from compared
where unemployment_rate is distinct from value
    and (year, quarter, sex) not in (
        (2011, 1, '男女計'), (2011, 1, '女'), (2011, 2, '男女計'), (2011, 2, '男'),
        (2011, 3, '男女計'), (2011, 4, '男'), (2015, 4, '男'), (2016, 2, '男女計'),
        (2016, 4, '男'), (2021, 1, '男'), (2021, 2, '男'), (2021, 2, '女'), (2021, 3, '女')
    )
union all
select null, null, null, null, null
from compared
having count(*) < (select count(*) from first_table)
