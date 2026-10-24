-- 毎月勤労統計調査（東京都）の就業形態別常用労働者数（1行 = 年 × 月または年平均 × 事業所規模 × 産業）
select
    year,
    period_type,
    month,
    establishment_size,
    industry_code,
    industry_name,
    general_employees_start,
    general_employees_added,
    general_employees_removed,
    general_employees,
    part_time_employees_start,
    part_time_employees_added,
    part_time_employees_removed,
    part_time_employees
from {{ ref('stg_labour_employment_by_employment_type') }}
order by year, month nulls last, establishment_size, industry_code
