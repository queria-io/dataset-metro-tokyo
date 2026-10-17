{# 外国人人口のステージング。
   人口を INTEGER に型変換し（原典は年により桁区切りのカンマを含む）、
   現在日（各年1月1日）を DATE で付与し、地域コードから区分を導出する。 #}

select
    cast(year as integer) as year,
    make_date(cast(year as integer), 1, 1) as as_of_date,
    area_code,
    area_name,
    case
        when area_code = '13000' then '総数'
        when area_code in ('13100', '13200', '13550', '13300', '13350') then '地域区分'
        when area_code in ('13360', '13380', '13400', '13420') then '支庁'
        else '区市町村'
    end as area_type,
    nationality,
    {{ stats_integer("replace(population, ',', '')") }} as population
from {{ ref('raw_foreign_population') }}
