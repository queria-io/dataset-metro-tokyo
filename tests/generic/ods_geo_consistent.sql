{# 地図表示用の列が壊れていないことを確かめる。geometry 列を持つ ods の mart モデルに付ける。

   見るもの:
   - 座標が日本の値域に入っている
   - geo_lat / geo_lon / geo_source / geo_level / geometry の有無が揃っている
   - geo_source / geo_level の値が語彙どおり
   - geo_source のラベルが実際に採用した値と合っている（source なら原典のまま、
     source_swapped なら緯度と経度が入れ替わっている）
   - ST_Point の引数順を取り違えていない（経度が X、緯度が Y） #}

{% test ods_geo_consistent(model) %}

select
    lat,
    lon,
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
    or geo_source not in ('source', 'source_swapped')
    or geo_level not in ('source')
    or (geo_source = 'source'
        and (geo_lat is distinct from lat or geo_lon is distinct from lon))
    or (geo_source = 'source_swapped'
        and (geo_lat is distinct from lon or geo_lon is distinct from lat))
    or (
        geometry is not null
        and (
            st_x(geometry) not between 122.0 and 154.5
            or st_y(geometry) not between 20.0 and 46.0
        )
    )

{% endtest %}
