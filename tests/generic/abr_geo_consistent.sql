{# 住所から求めた座標だけを持つモデルで、地図表示用の列が壊れていないことを確かめる。

   ods_geo_consistent は原典の lat / lon と突き合わせるので、原典が座標を持たない
   台帳（hokenjo）には使えない。こちらは ABR 由来の座標だけを見る。

   見るもの:
   - 座標が日本の値域に入っている
   - geo_lat / geo_lon / geo_source / geo_level / geometry の有無が揃っている
   - geo_source は 'abr' のみ（原典座標が無いので source / source_swapped は出ない）
   - geo_level が ABR の粒度の語彙どおり。市区町村代表点を採用していない
   - ST_Point の引数順を取り違えていない（経度が X、緯度が Y） #}

{% test abr_geo_consistent(model) %}

select
    geo_lat,
    geo_lon,
    geo_source,
    geo_level,
    geometry
from {{ model }}
where
    (geo_lat is not null and geo_lat not between 20.0 and 46.0)
    or (geo_lon is not null and geo_lon not between 122.0 and 154.5)
    or (geo_lat is null) <> (geo_lon is null)
    or (geo_source is null) <> (geo_lat is null)
    or (geo_level is null) <> (geo_lat is null)
    or (geometry is null) <> (geo_lat is null)
    or geo_source not in ('abr')
    or geo_level not in (
        'residential_detail', 'residential_block', 'machiaza_detail', 'machiaza'
    )
    or (
        geometry is not null
        and (
            st_x(geometry) not between 122.0 and 154.5
            or st_y(geometry) not between 20.0 and 46.0
        )
    )

{% endtest %}
