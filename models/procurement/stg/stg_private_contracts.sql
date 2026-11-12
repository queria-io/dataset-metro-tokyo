{# 随意契約の締結状況のステージング。整理番号を INTEGER、日付を DATE に型変換する。
   日付は pipelines/procurement.py が和暦（「令和 3年 7月20日」「R2.12.2」）から
   ISO 形式に直したもの。原典の表記は *_text に残す。 #}

select
    org_code,
    org_name,
    category,
    period_label,
    period_start_month,
    period_end_month,
    try_cast(seq_no as integer) as seq_no,
    title,
    business_type,
    contract_amount,
    contract_amount_text,
    try_cast(contract_date as date) as contract_date,
    contract_date_text,
    try_cast(performance_start as date) as performance_start,
    try_cast(performance_end as date) as performance_end,
    performance_period,
    contractor,
    contractor_area,
    reason,
    requesting_section,
    source_resource,
    source_url
from {{ ref('raw_private_contracts') }}
