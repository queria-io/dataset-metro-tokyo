-- 毎月勤労統計調査（東京都）の常用労働者数・パートタイム労働者比率（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    employees_start,
    employees_start_male,
    employees_start_female,
    employees_added,
    employees_added_male,
    employees_added_female,
    employees_removed,
    employees_removed_male,
    employees_removed_female,
    employees,
    employees_male,
    employees_female,
    part_time_ratio,
    part_time_ratio_male,
    part_time_ratio_female
from {{ ref('stg_labour_employment') }}
order by year, month nulls last, establishment_size, industry_code
