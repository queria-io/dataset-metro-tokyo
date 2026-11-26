{# 千人単位の区分で、4つの四半期の平均が labour_force_activity（年平均の第2表）の値と一致することを
   確かめる。年平均は各月の平均なので四半期の平均と同じになるはずで、千人単位の丸めの分だけ
   差が出る（差 1 まで許す）。
   2015年と2020年は除く。基準人口を切り替えた表（2017年1〜3月期・2022年1〜3月期）が
   2015年10〜12月期と2020年10〜12月期だけを新しい基準で計算し直しているので、その年の
   4四半期は基準が混ざり、平均が年平均と最大 19.75（千人）ずれる。
   率の区分は人数の平均とは違う計算になるので比べない。
   比べる行が 300 未満（2015・2020年を除いて405行ある）のときは、突き合わせが空振りしているので失敗させる。 #}

with quarterly_mean as (
    select year, sex, item, avg(value) as mean_value
    from {{ ref('labour_force_activity_quarterly') }}
    where unit = '千人' and year not in (2015, 2020)
    group by all
    having count(value) = 4
),

compared as (
    select q.year, q.sex, q.item, q.mean_value, a.value
    from quarterly_mean as q
    inner join {{ ref('labour_force_activity') }} as a using (year, sex, item)
)

select year, sex, item, mean_value, value, 'mean <> annual' as check_name
from compared
where abs(mean_value - value) > 1
union all
select null, null, null, null, null, 'too few rows compared'
where (select count(*) from compared) < 300
