-- 随意契約の締結状況（1行=1契約）
select *
from {{ ref('stg_private_contracts') }}
