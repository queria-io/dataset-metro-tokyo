{# 1行 = 指数の種類 × 年 × 月または年平均 × 事業所規模 × 産業であることを確かめる。
   産業符号は産業名から引いて付けているので、引き当てを誤ると別の産業と重なる。 #}

select
    index_type,
    year,
    month,
    establishment_size,
    industry_code,
    count(*) as row_count
from {{ ref('labour_index') }}
group by all
having industry_code = '' or industry_code is null or count(*) > 1
