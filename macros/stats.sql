{% macro stats_integer(column) -%}
    {#- 統計表の数値列を INTEGER にする。原典の '-'（該当なし）と空欄は NULL。 -#}
    try_cast(nullif(nullif(trim({{ column }}), ''), '-') as integer)
{%- endmacro %}

{% macro stats_decimal(column, scale=1) -%}
    {#- 統計表の小数の数値列（日数・時間・割合）を小数 scale 桁の DECIMAL にする。原典の '－'（該当なし）・'×'（秘匿）と空欄は NULL。 -#}
    try_cast(nullif(trim({{ column }}), '') as decimal(5, {{ scale }}))
{%- endmacro %}
