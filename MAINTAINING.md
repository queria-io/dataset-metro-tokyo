# 運用メモ

README.md はデータセットのページに表示されるので、取り込みの仕組みとビルドの詳細はここに置く。

## 自治体標準オープンデータセットの取り込み

取り込み対象は ods_datasets.yml で定義し、catalog のメタデータからリソースを判定・ダウンロードして列名を標準キーに正規化する。新標準（所在地_連結表記等）と旧推奨データセット形式（住所・都道府県名等）のヘッダー揺れはエイリアス辞書で吸収し、標準列にマッピングできない列は extras (JSON) に退避する。

取り込みは毎回全量再取得の洗い替え。1リソースの失敗（リンク切れ・ヘッダー不一致等）は
source_files に記録して隔離し、全体を止めない。リソースのホストは自治体ごとに分散して
いるためホスト別にリクエスト間隔を制御する（data.bodik.jp は2秒以上）。
同一 URL が複数リソースとして登録されている場合（同じファイルに上書き公開しつつ、更新時点
ごとにリソースを増やしている自治体がある）は最初の1件のみ取り込み、落とした側は
status=skipped / reason=duplicate_url で台帳に残す。新しい月のリソースが前の月と同じ
ファイルを指したまま登録されている例があり、その月はどこにも無い。台帳に行が無いと
取り込み側が落としたのか原典に無いのかを後から区別できない。名称が空の行（表末尾の
バージョン表記など）は実体を持たないため落とす。名称の列を持たない種別（ods.fire_hydrant）は
ods_datasets.yml の identity_column で判定に使う列を差し替える。

自治体のページには、別の種別の CSV が同じページに並ぶことがある。ページから拾うのは、
ファイル名が種別のスラッグに一致するか、リンクの文言に種別の名前（ods_datasets.yml の
title_patterns）が入っている CSV だけで、そのうえでカタログに登録された CSV と同じ
ヘッダー検査を通す。証明書の検証には certifi のルート証明書を使う。実行環境の OS の
ストアに無いルート証明書を使う自治体のサイトがある。

種別誤判定を弾くため、名称と所在地の両方をマッピングできないファイルは隔離する。
名称・所在地の列を持たない種別（ods.school_district / ods.fire_hydrant）は
ods_datasets.yml の required_columns で必須列を差し替える。

元データの値は補正せず原典のまま保持する。日付は自治体ごとに表記が異なる
（YYYY-MM-DD / YYYY/M/D / YYYY.M.D）ため DATE に正規化するが、「4月頃」「毎年1月1日」の
ような自由記述は推測せず NULL にする。

ods.population の重複解消:

月次で公開する自治体では、前の年の同月のファイルが新しい月のデータで上書きされたまま、
正しい名前のリソースも別に登録されることがある。同じ（自治体・調査年月日・地域）が
複数のリソースから入った場合は、リソースの最終更新時点が新しい側だけを残す
（macros/ods_latest_resource.sql）。どの月が収録できたかは ods.source_files で確かめられる

ods.source_files の記録:

公開自治体は種別ごとに一部のみで、このテーブルで確認できる。基本は1行=1リソースだが、
種別に一致しながら CSV リソースを1つも持たないパッケージ（PDF や Excel でだけ登録されて
いる場合）は、パッケージ単位で1行 status=skipped / reason=no_csv_resource を記録する。
これが無いと「CSV 以外で公開している」と「公開していない」を台帳から区別できない。
HTML のページへのリンクだけで登録されたパッケージは、そのページに置かれた CSV を
たどって取り込み、CSV ごとに1行（via_page_url にたどったページ）を記録する。
ページに種別の CSV が無ければ reason=no_csv_on_page、ページを開けなければ
reason=page_fetch_error になる

## ジオコーディング

pipelines/geocode.py が data/ods/*.ndjson と data/hokenjo/*.ndjson の住所を
abr-geocoder に通し、(組織コード, 住所) 単位で data/geocode/addresses.ndjson に出す。
ODS は原典の緯度経度を優先してここで補うだけだが、保健所台帳は緯度経度を持たないので
座標はすべてここから来る。

住所は自分の市区町村名から始まらないことがあり、そのままでは市区町村の代表点までしか
解決しない。東京都名と自治体名を必要に応じて前置してから渡す。ただし東京都の局が
公開したデータの組織名は「東京都デジタルサービス局」のような部局名なので、
市区町村名としては使わない。

すでに都道府県名で始まる住所には何も足さない。区市町村は都外に保養所などを持っており、
前置すると「東京都新宿区山梨県北杜市…」という存在しない住所ができる。前置した自治体の
町字と偶然一致すれば、全く別の場所の座標を採用してしまう。

市区町村代表点（coordinate_level = city）は採用しない。地図に出すと区役所にピンが
積み上がるだけで、位置の情報になっていない。

ABR データは市区町村コードを62件明示して取得する。都道府県コード 130001 を渡すと
住居表示データが落ちてこず地番マスターだけになり、丁目代表点までしか解決しなくなる。
地番は使わない（--target residential）。地番を使うと解決が地番側に寄って街区の解決を
奪い、住居表示の採用がかえって減る。

abrg は入力と同じ件数を返さない。隣接する2行を連結して1クエリにしてしまうことがあり、
連結された側は結果が返らない。突合は abrg が返す query.input を NFKC 正規化した文字列で
行い、解決しなかった住所は件数を数えて警告に出す。

ABR の配布元は国外からの取得に 403 を返し、GitHub のランナー（米国）からは取れない。
そのため日本から取得した abrg のデータ（database と cache、圧縮して約 270MB）を
50MB ずつの断片と目録に分けて assets.queria.io に置き、ビルドはまずそれを展開して
取得の代わりにする（pipelines/geocode.py の ABR_SNAPSHOT_URL が目録）。断片は目録の
SHA-256 で確かめる。展開できなかったときだけ配布元から取る。
作り直しは日本から scripts/refresh_abr_snapshot.py --upload で行い、出力された日付を
ABR_SNAPSHOT_DATE に書いて PR にする。CDN のキャッシュに古い中身が残らないよう、
置く名前には作った日付を入れて上書きしない。

abrg は取得元の HTTP ステータスを見ずに応答を保存するので、取得元がエラーページを返すと
HTML が .zip の名前で残り、abrg はそれを飛ばしたあと終了せずに止まることがある。
そのため abrg の実行は download 600 秒・ジオコーディング 300 秒で打ち切り、取得後に
zip として読めないファイルが残っていれば、その先頭と取得元の応答をログに出して
60 秒・180 秒の間隔で2回まで取り直す。それでも残れば失敗させる。

## stats.resident_population の原典の癖

原典の癖はステージングで吸収している。集計行（区部・市部・郡部・島部）は表の先頭と
各ブロックの見出しに2回現れるため 月 × 地域コード で1行に落とす（値は同一で、
2011年10月分までは郡部の見出しが「西多摩郡」名で載る）。2001年分は西多摩郡4町村の
地域コードが1つずつずれており（檜原村と奥多摩町がどちらも 13308）、2002年1月分以降の
原典と同じコードに直している。「地域階層」列は2020年1月〜2022年2月分だけ番号体系が
変わるため使わず、地域コードから区分を導出している。数値は原典のまま保持し、'-' は NULL。

## データ更新手順

パイプライン実行時に以下を行う。ビルドは `bash scripts/build.sh` で実行する（Queria に公開する）。

- pipelines/ckan.py: CKAN API からカタログメタデータ全量を取得し NDJSON で data/catalog/ に保存（毎回洗い替え）
- pipelines/childcare.py: catalog のメタデータから「社会福祉施設等一覧」の最新版を解決し、
  認可保育所・児童館の CSV をダウンロードして cp932 から UTF-8 に変換し data/childcare/ に保存。
  取り込んだ版・パッケージ・URL は data/childcare/source.ndjson に記録する（catalog の後に実行する）
- pipelines/hokenjo.py: 保健所台帳の配布ページから台帳ごとの CSV のリンクと時点を解決し、
  ダウンロードして共通キーに正規化し data/hokenjo/ に保存する。リンクの URL は更新のたびに
  変わるため固定せず、台帳名をページの本文から引き当てる。6種すべてが揃わなければ止める
  （ジオコーディングの前に実行する）
- pipelines/resident_population.py: catalog のメタデータから公開済みの最新月を解決し、
  2001年1月分からその月までの月次 CSV をダウンロードして共通キーに正規化し
  data/resident_population/ に保存する（catalog の後に実行する）。公開済みの月にも
  遡及訂正が入るため直近36か月分は毎回取得し直し、それより古い月は取得済みのファイルを使う。
  取り込んだ月・URL・行数は data/resident_population/source.ndjson に記録する
- pipelines/foreign_population.py: 外国人人口の時系列 CSV（1979年からの全年が1ファイル）を
  毎回ダウンロードし、和暦の年の列を西暦の縦持ちに直して data/foreign_population/ に保存する。
  取得元 URL と行数は data/foreign_population/source.ndjson に記録する
- pipelines/labour_earnings.py: 毎月勤労統計調査の年報の一覧ページから各年の年報を解決し、
  第1-1表・第1-2表の CSV をダウンロードして公表年の行を data/labour_earnings/ に保存する。
  ファイル名の付け方が年によって違うため URL は固定せず、表題の行で表を確かめる。
  取り込んだ年報・表・URL・行数は data/labour_earnings/source.ndjson に記録する
- pipelines/labour_hours.py: 同じ年報から第6-1表・第6-2表の CSV をダウンロードし、公表年の行を
  data/labour_hours/ に保存する。表は年報のページに並ぶ順番で選び、表題の行で確かめる
  （2024年報はファイル名の番号が1つずれている）
- pipelines/labour_employment.py: 同じ年報から第10-1表・第10-2表の CSV をダウンロードし、公表年の行を
  data/labour_employment/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_earnings_by_employment_type.py: 同じ年報から第2-1表・第2-2表の CSV をダウンロードし、
  公表年の行を data/labour_earnings_by_employment_type/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_hours_by_employment_type.py: 同じ年報から第7-1表・第7-2表の CSV をダウンロードし、
  公表年の行を data/labour_hours_by_employment_type/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_employment_by_employment_type.py: 同じ年報から第11-1表・第11-2表の CSV をダウンロードし、
  公表年の行を data/labour_employment_by_employment_type/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_earnings_by_size.py: 同じ年報から第3表の CSV をダウンロードし、
  公表年の行を data/labour_earnings_by_size/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_hours_by_size.py: 同じ年報から第8表の CSV をダウンロードし、
  公表年の行を data/labour_hours_by_size/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_hours_by_size_and_employment_type.py: 同じ年報から第9表の CSV をダウンロードし、
  公表年の行を data/labour_hours_by_size_and_employment_type/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_earnings_by_size_and_employment_type.py: 同じ年報から第4表の CSV をダウンロードし、
  公表年の行を data/labour_earnings_by_size_and_employment_type/ に保存する。表の選び方は pipelines/labour_hours.py と同じ
- pipelines/labour_bonus.py: 同じ年報から第5表の CSV をダウンロードし、産業ごとの行に年報の公表年を付けて
  data/labour_bonus/ に保存する。表に年・月の列が無いので、共有の _parse の代わりに専用の関数で読む。表の選び方は pipelines/labour_hours.py と同じ

## テスト

取り込みの判定ロジック（pipelines/）と、重複解消の規則（macros/）の単体テスト。
ネットワークにも DuckLake にもつながず、packages.ndjson の小さな実例や、
DuckDB のインメモリ DB に組み立てた数行で確かめる。

```bash
uv run --group dev pytest tests/pipelines -q
```

dev グループは `default-groups = []` で既定から外してある。ビルドは
`uv run queria sync` を通るので、既定に入れるとビルド環境にテスト依存が混ざる。

tests/generic/ の .sql は dbt の generic test で、こちらは dbt が実行する。
