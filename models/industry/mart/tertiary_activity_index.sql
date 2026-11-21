-- 東京都第3次産業活動指数（月次。1行 = 月 × 業種 × 指数の種類）
select
    year,
    month,
    index_type,
    item_code,
    item_name,
    item_name_en,
    item_class,
    weight,
    index_value
from {{ ref('stg_tertiary_activity_index') }}
order by year, month, index_type, item_code
