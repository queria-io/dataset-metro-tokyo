{# 東京の労働力（四半期平均の第1表）のステージング。区分の扱いは年平均の stg_labour_force と同じ。
   区分の見出し「〔就業状態〕／労働力人口／就業者数」を、〔〕の中の分類（category）と
   残りの区分（item）に分ける。〔〕の無い「15歳以上人口」は就業状態の分類に入れる。
   分類名の末尾の「(%)」「（%）」は単位の列（unit）に移し、「就業者の活動状況別内訳」は
   「活動状態別内訳」にそろえる。区分の全角数字と全角の読点は半角にする。
   2003年7〜9月期の表は「就業者（含休業者）」「完全失業者」、2003年10〜12月期と2004年1〜3月期の表は
   「就業者数（含休業者数）」と書くので、後の表の「就業者数」「完全失業者数」の形にそろえる
   （就業者はどの年も休業者を含む）。
   値は小数1桁の DECIMAL に型変換し、原典の「…」（該当なし）・「-」（前年同期が無い区分）と空欄は NULL。 #}

with source as (
    select
        cast(year as integer) as year,
        cast(quarter as integer) as quarter,
        regexp_extract(item, '^〔(.*?)〕', 1) as raw_category,
        case
            when item like '〔%' then regexp_replace(item, '^〔.*?〕／', '')
            else item
        end as raw_item,
        sex,
        value,
        previous_year_value,
        change,
        change_rate
    from {{ ref('raw_labour_force_quarterly') }}
)

select
    year,
    quarter,
    case
        when raw_category = '' then '就業状態'
        else replace(
            regexp_replace(raw_category, '\s*[（(]%[）)]$', ''),
            '活動状況別', '活動状態別'
        )
    end as category,
    array_to_string(
        list_transform(
            string_split(
                replace(
                    regexp_replace(
                        translate(raw_item, '０１２３４５６７８９', '0123456789'),
                        '（含休業者数?）', '', 'g'
                    ),
                    '，', ','
                ),
                '／'
            ),
            part -> case
                when part in ('就業者', '完全失業者', '自営業主', '家族従業者', '雇用者', '従業者', '休業者')
                    then part || '数'
                when part = '就業者（再掲）' then '就業者数（再掲）'
                else part
            end
        ),
        '／'
    ) as item,
    sex,
    case when raw_category like '%\%%' escape '\' then '%' else '千人' end as unit,
    try_cast(nullif(value, '') as decimal(8, 1)) as value,
    try_cast(nullif(previous_year_value, '') as decimal(8, 1)) as previous_year_value,
    try_cast(nullif(change, '') as decimal(8, 1)) as change,
    try_cast(nullif(change_rate, '') as decimal(8, 1)) as change_rate
from source
