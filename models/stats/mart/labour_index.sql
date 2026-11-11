-- 毎月勤労統計調査（東京都）の賃金・労働時間・常用雇用の指数（1行 = 指数の種類 × 年 × 月または年平均 × 事業所規模 × 産業）
select
    index_type,
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    base_year,
    index_value,
    change_rate
from {{ ref('stg_labour_index') }}
order by index_type, year, month nulls last, establishment_size, industry_code
