{# 規模・就業形態別の実労働時間の内訳が合計と一致することを確かめる。
   原典の表は 総実労働時間 = 所定内労働時間 + 所定外労働時間 の関係にあり、
   小数1桁の公表値のまま一般労働者・パートタイム労働者の全行で一致する。列の割り当てがずれると
   値は数値のまま入るので、型や NULL の検査では見つからない。秘匿で NULL の項を含む行は比べない。 #}

select
    year,
    month,
    establishment_size
from {{ ref('labour_hours_by_size_and_employment_type') }}
where general_total_hours <> general_scheduled_hours + general_overtime_hours
    or part_time_total_hours <> part_time_scheduled_hours + part_time_overtime_hours
