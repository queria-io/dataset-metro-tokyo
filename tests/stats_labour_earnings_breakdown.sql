{# 月間現金給与額の内訳が合計と一致することを確かめる。
   原典の表は 現金給与総額 = きまって支給する給与 + 特別に支払われた給与、
   きまって支給する給与 = 所定内給与 + 所定外給与 の関係にある。
   列の割り当てがずれると（年報で列が増減した場合など）金額は数値のまま入るので、
   型や NULL の検査では見つからない。秘匿で NULL の項を含む行は比べない。 #}

select
    year,
    month,
    establishment_size,
    industry_code
from {{ ref('labour_earnings') }}
where cash_earnings <> contractual_earnings + special_earnings
    or contractual_earnings <> scheduled_earnings + overtime_earnings
