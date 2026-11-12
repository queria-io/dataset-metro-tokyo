-- 物品買入れの発注予定（1行=1件。公開中の最新の半期だけ）
select *
from {{ ref('stg_planned_goods') }}
