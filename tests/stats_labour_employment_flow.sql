{# 常用労働者数の月中の増減が月末の値と一致することを確かめる。
   原典の表は 本月末労働者数 = 前月末労働者数 + 増加労働者数 − 減少労働者数 の関係にあり、
   月次の行では計・男・女のすべてで一致する（年平均の行は各項の平均なので比べない）。
   列の割り当てがずれると値は数値のまま入るので、型や NULL の検査では見つからない。
   秘匿で NULL の項を含む行は比べない。 #}

select
    year,
    month,
    establishment_size,
    industry_code
from {{ ref('labour_employment') }}
where period_type = '月次'
    and (
        employees <> employees_start + employees_added - employees_removed
        or employees_male <> employees_start_male + employees_added_male - employees_removed_male
        or employees_female <> employees_start_female + employees_added_female - employees_removed_female
    )
