{% macro stats_integer(column) -%}
    {#- 統計表の数値列を INTEGER にする。原典の '-'（該当なし）と空欄は NULL。 -#}
    try_cast(nullif(nullif(trim({{ column }}), ''), '-') as integer)
{%- endmacro %}

{% macro stats_decimal(column) -%}
    {#- 統計表の小数1桁の数値列（日数・時間）を DECIMAL にする。原典の '－'（該当なし）・'×'（秘匿）と空欄は NULL。 -#}
    try_cast(nullif(trim({{ column }}), '') as decimal(5, 1))
{%- endmacro %}
