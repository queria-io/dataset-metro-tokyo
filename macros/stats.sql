{% macro stats_integer(column) -%}
    {#- 統計表の数値列を INTEGER にする。原典の '-'（該当なし）と空欄は NULL。 -#}
    try_cast(nullif(nullif(trim({{ column }}), ''), '-') as integer)
{%- endmacro %}
