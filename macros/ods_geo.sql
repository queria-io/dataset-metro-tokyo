{# ODS の緯度経度から「地図に出せる座標」を決める。

   自治体標準オープンデータセットの緯度・経度は自治体が公開した値をそのまま入れており、
   緯度と経度が入れ替わっている自治体（ods.cultural_property の豊島区は全行）や、
   小数点が欠落している行（ods.event）がある。原典の lat / lon は補正せずに残し、
   地図に使える座標を geo_lat / geo_lon として別に持たせる。

   geo_source は採用した値の由来。
     source          原典の緯度経度をそのまま採用した
     source_swapped  原典の緯度と経度が入れ替わっていたので入れ替えて採用した
     NULL            採用できる座標がない（欠損または値域外）

   geo_level は座標の粒度。原典由来の座標は粒度が申告されないので 'source' 固定。
   値の語彙は abr-geocoder の matchLevel に揃えてあり、ジオコーディングで補完した
   座標が入ると 'rsdtdsp_blk' 等が加わる。 #}

{# 値域は東京都ではなく日本全域にとる。都外の所在地を持つ行（食品営業許可の本社住所など）
   が実在し、東京都に絞ると原典の正しい座標を捨ててしまうため。
   緯度域 [20.0, 46.0] と経度域 [122.0, 154.5] は重ならないので、これでも入れ替わりは
   一意に判定できる（緯度に 139 が入れば緯度域を外れ、経度に 35 が入れば経度域を外れる）。
   端は沖ノ鳥島 北緯 20.42 / 択捉島 北緯 45.55 / 与那国島 東経 122.93 / 南鳥島 東経 153.98。 #}
{% macro ods_geo_in_range(lat, lon) -%}
({{ lat }} between 20.0 and 46.0 and {{ lon }} between 122.0 and 154.5)
{%- endmacro %}

{% macro ods_geo_columns(lat='try_cast(lat as double)', lon='try_cast(lon as double)') -%}
case
        when {{ ods_geo_in_range(lat, lon) }} then {{ lat }}
        when {{ ods_geo_in_range(lon, lat) }} then {{ lon }}
    end as geo_lat,
    case
        when {{ ods_geo_in_range(lat, lon) }} then {{ lon }}
        when {{ ods_geo_in_range(lon, lat) }} then {{ lat }}
    end as geo_lon,
    case
        when {{ ods_geo_in_range(lat, lon) }} then 'source'
        when {{ ods_geo_in_range(lon, lat) }} then 'source_swapped'
    end as geo_source,
    case
        when {{ ods_geo_in_range(lat, lon) }} or {{ ods_geo_in_range(lon, lat) }} then 'source'
    end as geo_level
{%- endmacro %}

{# 地図表示用のジオメトリ。座標が無い行は NULL にする。
   ST_Point(NULL, NULL) はジオメトリを返してしまい、地図プレビューの件数に混ざる。
   1 テーブルに GEOMETRY 列は 1 本だけにすること（プレビュー生成も queria-web も
   最初の GEOMETRY 列しか見ない）。 #}
{% macro ods_geometry(lat='geo_lat', lon='geo_lon') -%}
case when {{ lat }} is not null then st_point({{ lon }}, {{ lat }}) end
{%- endmacro %}
