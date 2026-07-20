# dataset-metro-tokyo

東京都オープンデータカタログ（catalog.data.metro.tokyo.lg.jp）で公開されるデータを DuckLake カタログ化したデータセット。

## データ出典

- 東京都オープンデータカタログ: https://catalog.data.metro.tokyo.lg.jp/
  - catalog スキーマ: CKAN API（package_search / organization_list / group_list）から取得したメタデータ
- 東京都福祉局「社会福祉施設等一覧（令和7年5月1日時点）」のうち、認可保育所と児童館の CSV。緯度経度は十進度、座標系は JGD2011
  - 認可保育所: https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-1-hoikusyo.csv
  - 児童館: https://www.opendata.metro.tokyo.lg.jp/fukushi/202505-2-2_06-zidoukan.csv

## スキーマ: catalog（カタログメタデータ）

東京都オープンデータカタログに登録された全データセット（約9,600件）のメタデータ台帳。
都庁各局と都内62区市町村が提供するオープンデータの全体像を SQL で俯瞰できる。
CKAN API から毎回全量を取得して洗い替える。

- catalog.datasets: 全データセット一覧（タイトル・提供組織・ライセンス・更新頻度・metadata_modified・ポータルURL）
- catalog.resources: 全リソース（配布ファイル）一覧（フォーマット・ダウンロードURL・更新日時）。
  リソース URL はファイル更新で変わることがあるため、常に本テーブルの最新 URL を参照する
- catalog.organizations: 提供組織一覧（組織コード・組織種別: 都庁各局/特別区/市/町村）
- catalog.groups: 分野分類（16分類）
- catalog.dataset_tags: データセット×タグ（「自治体標準オープンデータセット」「都知事杯ハッカソン」等）
- catalog.dataset_groups: データセット×分野分類

## スキーマ: ods（自治体標準オープンデータセット）

都内区市町村が公開する「自治体標準オープンデータセット」（デジタル庁 データセット定義書A）を
種別ごとに区市町村横断で統合したテーブル群。取り込み対象は ods_datasets.yml で定義し、
catalog のメタデータからリソースを判定・ダウンロードして列名を標準キーに正規化する。
新標準（所在地_連結表記等）と旧推奨データセット形式（住所・都道府県名等）のヘッダー揺れは
エイリアス辞書で吸収し、標準列にマッピングできない列は extras (JSON) に退避する。

- ods.evacuation_space: 指定緊急避難場所一覧（災害種別対応可否を BOOLEAN 化）
- ods.aed: AED設置箇所一覧（設置位置・利用可能日時・小児対応設備）
- ods.preschool: 子育て施設一覧（種別・収容定員・一時預かり/病児保育）
- ods.hospital: 医療機関一覧（診療科目・病床数・災害拠点分類。都保健医療局の都全域データ含む）
- ods.public_wireless_lan: 公衆無線LANアクセスポイント一覧（SSID・提供エリア）
- ods.public_facility: 公共施設一覧（名称・所在地・連絡先・利用可能時間・アクセス方法。公民館・図書館・区民施設等）
- ods.public_toilet: 公衆トイレ一覧（便器数・バリアフリートイレ数・車椅子使用者用/乳幼児用設備/オストメイトの有無）
- ods.cultural_property: 文化財一覧（文化財分類・種類・員数・所有者・文化財指定日）
- ods.tourism: 観光施設一覧（POIコード・利用可能時間・料金・アクセス方法・バリアフリー情報）
- ods.event: イベント一覧（開催日・会場・料金・定員・申込方法。祭り・講座・展示等）
- ods.school_district: 小中学校通学区域情報（学校×通学区域。区域の住所はセミコロン区切り）
- ods.fire_hydrant: 消防水利施設一覧（消火栓・防火水槽・プール・河川等の位置と口径）
- ods.source_files: 取り込みの実行結果（1行=1リソース）。自治体カバレッジ・失敗理由・
  エンコーディングの記録。公開自治体は種別ごとに一部のみで、このテーブルで確認できる

取り込みは毎回全量再取得の洗い替え。1リソースの失敗（リンク切れ・ヘッダー不一致等）は
source_files に記録して隔離し、全体を止めない。リソースのホストは自治体ごとに分散して
いるためホスト別にリクエスト間隔を制御する（data.bodik.jp は2秒以上）。
同一 URL が複数リソースとして登録されている場合（同じファイルに上書き公開しつつ、更新時点
ごとにリソースを増やしている自治体がある）は最初の1件のみ取り込む。名称が空の行（表末尾の
バージョン表記など）は実体を持たないため落とす。名称の列を持たない種別（ods.fire_hydrant）は
ods_datasets.yml の identity_column で判定に使う列を差し替える。

種別誤判定を弾くため、名称と所在地の両方をマッピングできないファイルは隔離する。
名称・所在地の列を持たない種別（ods.school_district / ods.fire_hydrant）は
ods_datasets.yml の required_columns で必須列を差し替える。

元データの値は補正せず原典のまま保持する。ods.cultural_property では緯度と経度が
入れ替わったまま公開されている自治体があり（豊島区の全行）、ods.event でも緯度経度が
入れ替わっている自治体・経度の小数点が欠落している自治体があるため、地図表示の前に
値域の確認が要る。日付は自治体ごとに表記が異なる（YYYY-MM-DD / YYYY/M/D / YYYY.M.D）ため
DATE に正規化するが、「4月頃」「毎年1月1日」のような自由記述は推測せず NULL にする。

ods.school_district は施設一覧ではなく学校×通学区域の一覧で、所在地・緯度経度の列を持たない
（学校の位置は nlftp.facility.school を参照）。町丁目ごとに学校名を並べる独自形式で
通学区域を公開している自治体は標準形式ではないため収録していない。

ods.fire_hydrant は定義上そもそも名称の列を持たず、種別（消火栓・防火水槽・プール・河川等）で
水利を識別する。種別に統制語彙が無いため表記は自治体ごとに揺れる（防火水槽 / 防火水そう など）が、
原典のまま保持する。管轄・水利番号を並べる独自様式で公開している自治体は収録していない。

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

パイプライン実行時に以下を行う。ビルドは `bash scripts/build.sh local` で実行する。

- pipelines/ckan.py: CKAN API からカタログメタデータ全量を取得し NDJSON で data/catalog/ に保存（毎回洗い替え）
- pipelines/childcare.py: 認可保育所・児童館の CSV をダウンロードし、cp932 から UTF-8 に変換して data/childcare/ に保存

## ライセンス

クリエイティブ・コモンズ 表示 4.0 国際（CC BY 4.0）に従う。出典データは加工して利用している。

- 出典: 東京都福祉局「社会福祉施設等一覧（令和7年5月1日時点）」（東京都オープンデータカタログ）
- ライセンス: https://creativecommons.org/licenses/by/4.0/deed.ja
