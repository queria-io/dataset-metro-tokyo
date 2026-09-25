{# 性別の判定が片方に寄っていないことを確かめる。
   population_by_age は population の age_*_male / age_*_female を縦持ちにしたもので、
   地域 × 調査年月日 × 年齢階級には男性と女性の行が1本ずつ現れる。
   判定が崩れて片方に寄ると（LIKE の `_` が female を male として拾った実例がある）、
   人口の総数は合ったまま性別だけが誤るので、総数の検査では見つからない。

   同じ性別に2行以上寄り、もう片方が無い組を失敗とする。
   元データの片方の性別が空欄だと UNPIVOT がその行を落とし、1行だけ残る。
   これは原典の欠けで判定の誤りではないので、1行だけの組は失敗にしない。 #}

select
    organization_name,
    survey_date,
    area_name,
    age_band
from {{ ref('population_by_age') }}
group by all
having count(distinct sex) = 1
    and count(*) >= 2
