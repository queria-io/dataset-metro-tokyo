{# 実労働時間の内訳が合計と一致することを確かめる。
   原典の表は 総実労働時間 = 所定内労働時間 + 所定外労働時間 の関係にあり、
   小数1桁の公表値のまま全行で一致する。列の割り当てがずれると値は数値のまま入るので、
   型や NULL の検査では見つからない。秘匿で NULL の項を含む行は比べない。 #}

select
    year,
    month,
    establishment_size,
    industry_code
from {{ ref('labour_hours') }}
where total_hours <> scheduled_hours + overtime_hours
    or total_hours_male <> scheduled_hours_male + overtime_hours_male
    or total_hours_female <> scheduled_hours_female + overtime_hours_female
