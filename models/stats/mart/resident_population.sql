-- 住民基本台帳による世帯と人口（東京都・月次。1行 = 月 × 地域）
select
    year_month,
    as_of_date,
    area_code,
    area_name,
    area_type,
    population_total,
    population_change,
    japanese_total,
    japanese_male,
    japanese_female,
    foreign_total,
    foreign_male,
    foreign_female,
    household_total,
    household_japanese_only,
    household_foreign_only,
    household_mixed
from {{ ref('stg_resident_population') }}
order by year_month, area_code
