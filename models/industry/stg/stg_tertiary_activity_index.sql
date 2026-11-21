{# 東京都第3次産業活動指数（月次）のステージング。
   指数・ウェイトを DECIMAL に型変換する。値が「―」の月（その業種の系列がまだ無い月）は NULL。
   品目階層は 0 = 第3次産業総合、1〜5 = 大分類〜細々分類、11・12 = 再編集系列。 #}

select
    cast(year as integer) as year,
    cast(month as integer) as month,
    index_type,
    item_code,
    item_name,
    item_name_en,
    cast(item_class as integer) as item_class,
    try_cast(weight as decimal(8, 1)) as weight,
    try_cast(nullif(value, '') as decimal(6, 1)) as index_value
from {{ ref('raw_tertiary_activity_index') }}
