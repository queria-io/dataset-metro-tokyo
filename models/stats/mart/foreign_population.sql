-- 外国人人口（東京都・各年1月1日現在。1行 = 年 × 地域 × 国籍・地域）
select
    year,
    as_of_date,
    area_code,
    area_name,
    area_type,
    nationality,
    population
from {{ ref('stg_foreign_population') }}
order by year, area_code, nationality
