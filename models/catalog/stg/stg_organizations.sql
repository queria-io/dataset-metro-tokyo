{# 提供組織のステージング。組織コード（JIS 全国地方公共団体コード準拠）から
   組織種別（都庁各局 / 特別区 / 市 / 町村）を導出する。
   t134xxx は島嶼町村と非自治体（GovTech東京等）が混在するため、
   島嶼3自治体のみフルコードで指定し、残りは「その他」（政策連携団体等）に落とす。 #}

select
    name as organization_code,
    title,
    description,
    case
        -- 島嶼町村（八丈町・青ヶ島村・小笠原村）
        when name in ('t134015', 't134023', 't134210') then '町村'
        when name like 't000%' or name = 't313360' then '都庁各局'
        when name like 't131%' then '特別区'
        when name like 't132%' then '市'
        when name like 't133%' then '町村'
        else 'その他'
    end as organization_type,
    try_cast(package_count as integer) as dataset_count,
    try_cast(created as timestamp) as created
from {{ ref('raw_organizations') }}
