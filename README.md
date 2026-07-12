# dataset-metro-tokyo

東京都オープンデータカタログ（catalog.data.metro.tokyo.lg.jp）で公開されるデータを DuckLake カタログ化したデータセット。

## データ出典

東京都福祉局「社会福祉施設等一覧（令和7年5月1日時点）」のうち、認可保育所と児童館の CSV を使用する。緯度経度は十進度、座標系は JGD2011。

- 東京都オープンデータカタログ: https://catalog.data.metro.tokyo.lg.jp/
- 認可保育所: https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-1-hoikusyo.csv
- 児童館: https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-2_06-zidoukan.csv

## テーブル: childcare.nursery_school

東京都内の認可保育所の一覧（3,581施設、令和7年5月1日時点）。

- establisher_type: 設置（設置主体の区分。区市町村立・私立等）
- name: 施設名
- postal_code: 郵便番号
- address: 所在地（都道府県名を含まない。「千代田区外神田…」形式）
- lon: 経度（十進度、JGD2011）
- lat: 緯度（十進度、JGD2011）
- crs: 座標系（元データに記載された座標系。JGD2011）
- phone_number: 電話番号
- capacity: 認可定員（人。元データの '-' や空欄は NULL）

## テーブル: childcare.children_center

東京都内の児童館の一覧（590施設、令和7年5月1日時点）。

- establisher_type: 設置（設置主体の区分。区市町村立・私立等）
- name: 施設名
- postal_code: 郵便番号
- address: 所在地（都道府県名を含まない。「千代田区外神田…」形式）
- lon: 経度（十進度、JGD2011）
- lat: 緯度（十進度、JGD2011）
- crs: 座標系（元データに記載された座標系。JGD2011）
- phone_number: 電話番号
- capacity: 定員（人。元データの '-' や空欄は NULL）

### データ更新手順

pipelines/childcare.py がパイプライン実行時に認可保育所・児童館の CSV をダウンロードし、
cp932 から UTF-8 に変換して data/childcare/ に保存する。
ビルドは `bash scripts/build.sh local` で実行する。

## ライセンス

クリエイティブ・コモンズ 表示 4.0 国際（CC BY 4.0）に従う。出典データは加工して利用している。

- 出典: 東京都福祉局「社会福祉施設等一覧（令和7年5月1日時点）」（東京都オープンデータカタログ）
- ライセンス: https://creativecommons.org/licenses/by/4.0/deed.ja
