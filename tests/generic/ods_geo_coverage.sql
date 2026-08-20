{# 原典が緯度経度を持つ行のうち、地図に出せる座標として採用できた割合の下限を見る。

   ods_geo_consistent が見る不変条件は ods_geo_columns の構成から自動的に成り立つので、
   値域を書き間違えて大半の行を落としても「一貫して NULL」になるだけで検出できない。
   ビルドは無人で走り push まで進むため、件数側の下限をここで押さえる。

   分母は「原典が緯度と経度の対を持つ行」にする。count(lat) だと経度が欠けた行も数え、
   自治体が緯度だけ公開した CSV を出すとこちらのロジックが変わっていなくても比率が
   下がる。取得元の不備でビルドが落ちると、データセット全体の公開が止まってしまう。

   既定の 0.95 は実測（16種別すべてで 0.98 以上、最小は ods.event の 0.990）から取る。 #}

{% test ods_geo_coverage(model, min_ratio=0.95) %}

select
    count(*) filter (where lat is not null and lon is not null) as source_rows,
    count(geo_lat) as adopted_rows,
    count(geo_lat) * 1.0
        / count(*) filter (where lat is not null and lon is not null) as ratio
from {{ model }}
having count(*) filter (where lat is not null and lon is not null) > 0
   and count(geo_lat) * 1.0
       / count(*) filter (where lat is not null and lon is not null) < {{ min_ratio }}

{% endtest %}
