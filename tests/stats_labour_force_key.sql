{# 1行 = 年 × 分類 × 区分 × 男女であることと、実数が空でないことを確かめる。
   分類は区分の見出しの〔〕から切り出しているので、切り出しに失敗すると
   分類が空になるか、別の区分と重なる。 #}

select
    year,
    category,
    item,
    sex,
    count(*) as row_count
from {{ ref('labour_force') }}
group by all
having category = '' or item = '' or count(*) > 1 or count(value) < count(*)
