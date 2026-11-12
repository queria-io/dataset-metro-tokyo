{# 東京都の完全失業率が、labour_force（その年の表の第1表）の完全失業率の総数と一致することを確かめる。
   参考表は最も新しい年の表の値を使うので、後の年の表で改訂された年は一致しない。
   原典で食い違うのは 2011年の女（その年の表 4.6、2012年からの表 4.7）だけ。
   分類名が変わって結合が0件になったときも、比べた年が足りないものとして落とす。 #}

with rate as (
    select year, sex, unemployment_rate
    from {{ ref('labour_force_unemployment_rate') }}
    where area = '東京都'
),

first_table as (
    select year, sex, value
    from {{ ref('labour_force') }}
    where category = '完全失業率（年齢階級別）'
        and item = '総数'
),

compared as (
    select rate.year, rate.sex, rate.unemployment_rate, first_table.value
    from rate
    inner join first_table using (year, sex)
)

select year, sex, unemployment_rate, value
from compared
where unemployment_rate is distinct from value
    and not (year = 2011 and sex = '女')
union all
select null, null, null, null
from compared
having count(*) < (select count(*) from first_table)
