{# 1行 = 年 × 事業所規模 × 産業であることを確かめる。
   産業符号は原典の文字列から切り出しているので、符号と名前の間の空白が無い行などで
   切り出しに失敗すると、符号が空になるか別の産業と重なる。 #}

select
    year,
    establishment_size,
    industry_code,
    count(*) as row_count
from {{ ref('labour_bonus') }}
group by all
having industry_code = '' or industry_code is null or count(*) > 1
