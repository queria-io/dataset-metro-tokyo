{# ジオコーディング結果のステージング。ods の各種別が住所で引く。

   採用しない粒度（市区町村代表点など）は pipelines/geocode.py が geo_lat を NULL に
   して出しているので、ここでは座標が入っている行だけに絞る。地図に出せない行を
   残すと、左結合した先で「結果はあるが座標は無い」を各モデルが判定することになる。

   (org_code, address) は pipelines/geocode.py の出力で一意。念のためここで畳んで、
   左結合が行を増やさないことをモデル側で気にしなくてよいようにする。 #}

select
    org_code,
    address,
    any_value(geo_lat) as geo_lat,
    any_value(geo_lon) as geo_lon,
    any_value(geo_level) as geo_level,
    any_value(lg_code) as lg_code,
    any_value(machiaza_id) as machiaza_id,
    any_value(pref) as pref,
    any_value(city) as city,
    any_value(ward) as ward,
    any_value(oaza_cho) as oaza_cho,
    any_value(chome) as chome,
    any_value(koaza) as koaza,
    any_value(blk_num) as blk_num,
    any_value(rsdt_num) as rsdt_num,
    any_value(rsdt_num2) as rsdt_num2,
    any_value(match_level) as match_level
from {{ ref('raw_geocode') }}
where geo_lat is not null
group by org_code, address
