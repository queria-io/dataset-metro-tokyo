{# ODS の日付列を DATE に正規化する。
   自治体により YYYY-MM-DD / YYYY/M/D / YYYY.M.D の表記が混在するため複数書式を試す。
   どの書式でも解釈できない値（Excel のシリアル値・自由記述など）は NULL。 #}

{% macro ods_date(column) -%}
coalesce(
    try_cast({{ column }} as date),
    try_strptime({{ column }}, '%Y.%m.%d')::date
)
{%- endmacro %}
