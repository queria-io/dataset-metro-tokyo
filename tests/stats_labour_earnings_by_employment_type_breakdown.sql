{# 就業形態別の月間現金給与額の内訳が合計と一致することを確かめる。
   原典の表は一般労働者・パートタイム労働者のそれぞれで
   現金給与総額 = きまって支給する給与 + 特別に支払われた給与、
   きまって支給する給与 = 所定内給与 + 所定外給与 の関係にある。
   列の割り当てがずれると金額は数値のまま入るので、型や NULL の検査では見つからない。
   秘匿で NULL の項を含む行は比べない。 #}

select
    year,
    month,
    establishment_size,
    industry_code
from {{ ref('labour_earnings_by_employment_type') }}
where general_cash_earnings <> general_contractual_earnings + general_special_earnings
    or general_contractual_earnings <> general_scheduled_earnings + general_overtime_earnings
    or part_time_cash_earnings <> part_time_contractual_earnings + part_time_special_earnings
    or part_time_contractual_earnings <> part_time_scheduled_earnings + part_time_overtime_earnings
