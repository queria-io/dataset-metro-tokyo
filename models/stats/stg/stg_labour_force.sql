{# 東京の労働力（年平均の第1表）のステージング。
   区分の見出し「〔就業状態〕／労働力人口／就業者数」を、〔〕の中の分類（category）と
   残りの区分（item）に分ける。〔〕の無い「15歳以上人口」は就業状態の分類に入れる
   （労働力人口と非労働力人口の合計にあたる）。
   分類名の末尾の「(%)」「（%）」は単位の列（unit）に移す。2004年と2020〜2023年の表で
   「就業者の活動状況別内訳」と書かれている分類は、他の年の「活動状態別内訳」にそろえる。
   区分の全角数字と全角の読点は半角にする。
   値は小数1桁の DECIMAL に型変換し、原典の「…」（該当なし）・「-」（前年が無い区分）と空欄は NULL。 #}

with source as (
    select
        cast(year as integer) as year,
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
    from {{ ref('raw_labour_force') }}
)

select
    year,
    case
        when raw_category = '' then '就業状態'
        else replace(
            regexp_replace(raw_category, '\s*[（(]%[）)]$', ''),
            '活動状況別', '活動状態別'
        )
    end as category,
    replace(translate(raw_item, '０１２３４５６７８９', '0123456789'), '，', ',') as item,
    sex,
    case when raw_category like '%\%%' escape '\' then '%' else '千人' end as unit,
    try_cast(nullif(value, '') as decimal(8, 1)) as value,
    try_cast(nullif(previous_year_value, '') as decimal(8, 1)) as previous_year_value,
    try_cast(nullif(change, '') as decimal(8, 1)) as change,
    try_cast(nullif(change_rate, '') as decimal(8, 1)) as change_rate
from source
