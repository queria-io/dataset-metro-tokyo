{# 就業形態別の常用労働者数が、就業形態を合わせた計と一致することを確かめる。
   原典では一般労働者とパートタイム労働者の本月末労働者数の和が第10表の本月末労働者数と
   月次・年平均の全行で一致する。月次の行では2つを合わせた増減も月末の値と一致する
   （就業形態ごとには一致しない）。
   列の割り当てがずれると値は数値のまま入るので、型や NULL の検査では見つからない。
   秘匿で NULL の項を含む行は比べない。 #}

select
    t.year,
    t.month,
    t.establishment_size,
    t.industry_code
from {{ ref('labour_employment_by_employment_type') }} as t
inner join {{ ref('labour_employment') }} as e
    on t.year = e.year
    and t.period_type = e.period_type
    -- 年平均の行は month が NULL なので、= では結合されない
    and t.month is not distinct from e.month
    and t.establishment_size = e.establishment_size
    and t.industry_code = e.industry_code
where t.general_employees + t.part_time_employees <> e.employees
    or (
        t.period_type = '月次'
        and t.general_employees + t.part_time_employees
            <> t.general_employees_start + t.part_time_employees_start
            + t.general_employees_added + t.part_time_employees_added
            - t.general_employees_removed - t.part_time_employees_removed
    )
