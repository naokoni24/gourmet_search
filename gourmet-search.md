# Googleグルメサーチ 仕様書

更新日: 2026-07-04
リポジトリ: `https://github.com/naokoni24/gourmet_search.git`
ブランチ: `main`

## 運用ルール

このプロジェクトを修正する時は、毎回このObsidianノートを読み込んでから作業します。

作業後は以下を行います。

- 実装内容に合わせてこの `gourmet-search.md` を更新
- リポジトリへ同期: `cp "/Users/nao/Documents/Obsidian Vault/gourmet-search/gourmet-search.md" /Users/nao/Desktop/projects/gourmet-search/gourmet-search.md`
- コミットして `origin main`（`https://github.com/naokoni24/gourmet_search.git`）へ必ずpushする（確認なしでpushしてよい）

---

## 概要

Google Places API (New) を使い、駅名・エリア名 または 現在地の近くの飲食店を検索するWebアプリ。キーワード・ジャンル・距離・予算・評価で絞り込み、評価降順で最大60件表示する。

## 基本情報

| 項目 | 内容 |
|---|---|
| アプリ名 | Googleグルメサーチ |
| GitHub | https://github.com/naokoni24/gourmet_search |
| フロントエンド ローカル起動 | `npm run dev`（`http://localhost:3000`、デフォルトで `http://localhost:8000` のバックエンドを呼ぶ） |
| バックエンド ローカル起動 | `cd backend && uvicorn app.main:app --reload`（`http://localhost:8000`） |
| フロントエンド デプロイ | Vercel（想定） |
| バックエンド デプロイ | Render（`backend/Procfile` で `uvicorn app.main:app --host 0.0.0.0 --port $PORT` を起動、`runtime.txt` は `python-3.12`） |

## 技術スタック

### フロントエンド (`/`)

| 種類 | 内容 |
|---|---|
| フレームワーク | Next.js 16 (App Router) + React 19 |
| 言語 | TypeScript |
| スタイル | Tailwind CSS 4 |
| アイコン | lucide-react |
| 認証 | 独自の簡易パスワード認証（Cookie） |

### バックエンド (`backend/`)

| 種類 | 内容 |
|---|---|
| フレームワーク | FastAPI（Python 3.12） |
| サーバー | uvicorn |
| HTTPクライアント | httpx |
| データモデル | pydantic |
| 検索先API | Google Places API (New) — Text Search / Nearby Search |

`backend/requirements.txt` には `feedparser` / `beautifulsoup4` / `lxml` も含まれるが、現状のコード（`app/api`, `app/crawlers`, `app/models`）では未使用。

## 環境変数

### バックエンド (`backend/.env`)

| 変数 | 必須 | 内容 |
|---|---|---|
| `GOOGLE_PLACES_API_KEY` | 検索には必須 | Google Places API (New) のAPIキー。未設定時は検索結果が常に空になる |
| `HOTPEPPER_API_KEY` | 未使用 | `.env.example` に残っているが、現在のクローラーは Google Places のみで参照していない |
| `ALLOWED_ORIGINS` | 任意 | CORS許可オリジン（カンマ区切り）。未設定時は `http://localhost:3001` |

### フロントエンド

| 変数 | 必須 | 内容 |
|---|---|---|
| `BACKEND_URL` | 任意 | `/api/search` のプロキシ先。未設定時は `http://localhost:8000` |
| `AUTH_PASSWORD` | ログイン機能には必須 | ログインパスワード（平文比較） |
| `AUTH_TOKEN_VALUE` | ログイン機能には必須 | 認証成功時にCookieへ入れる固定トークン文字列 |

## 認証

- `/login` でパスワードを入力し `POST /api/auth/login` に送信。`AUTH_PASSWORD` と一致すれば `auth_token` Cookie（httpOnly, 30日）に `AUTH_TOKEN_VALUE` を設定する。
- `src/proxy.ts`（middleware）が `/login` と `/api/auth/*` 以外の全パスで `auth_token` Cookieを検証し、欠如・不一致の場合は `/login` にリダイレクトする。
- ログアウトは `POST /api/auth/logout` でCookieを削除するのみ（サーバー側にセッション管理は無い、単一共有パスワード方式）。

## 画面構成

```
/       検索フィルタ + 結果一覧（トップページ）
/login  ログイン
```

## iPhoneホーム画面アイコン

- `src/app/apple-icon.png`（180x180, 不透明PNG）を配置。Next.jsのApp Router慣習により自動で `<link rel="apple-touch-icon" sizes="180x180" href="/apple-icon.png?...">` が出力される（コード生成ではなく画像ファイル方式）。
- 元画像はユーザー提供の「オレンジ〜赤のピンに黄色い星＋フォークとスプーン」のアイコン（`/Users/nao/Desktop/icon.png`、1254x1254）。この元画像はプレビュー用に角丸＋背景透過が黒（アルファ無し）へ焼き込まれた状態だったため、四隅の黒い部分（半径約209px相当）を除去する目的で各辺225pxをクロップ→180x180にリサイズしてフルブリード（角丸なし・不透明）な正方形画像を作成した。iOS側が独自に角丸マスクを適用する前提のため、アイコン画像自体は角丸を付けない。
- 【不具合修正】導入直後、iPhoneのホーム画面に「追加」し直してもアイコンが切り替わらない不具合があった。原因は `src/proxy.ts` の認証ミドルウェアが `/login` と `/api/auth/*` 以外の全パス（`/apple-icon.png` を含む）にCookie認証を要求していたこと。iOSの「ホーム画面に追加」によるアイコン取得はページのJS `fetch` とは異なる経路で行われ、認証Cookieが渡らずログイン画面へリダイレクトされてしまい、正しい画像を取得できずスクリーンショット等のフォールバック表示になっていたと考えられる。rss-generatorプロジェクトでも同様の理由でアイコン/manifestを認証前に配信する対応をしていた前例がある。
  - 修正: `src/proxy.ts` の認証不要パス判定に `pathname === '/apple-icon.png'` を追加し、OSがログイン状態に関わらずアイコン画像を取得できるようにした（`/` など他のページは引き続き認証必須のまま）。
  - ローカルで未ログイン状態のまま `fetch('/apple-icon.png')` が200 OK・`image/png`で返り、`/` は依然ログイン画面へリダイレクトされることを確認済み。
  - この修正を反映した上で、iPhone側は既存のホーム画面アイコンを削除→Safariで開き直して再度「ホーム画面に追加」する必要がある（iOSは追加時点のスナップショットを保持するため）。
- 【デザイン変更】アイコン画像を、青・赤・黄・緑のGoogleカラーの虫眼鏡＋皿にフォークとスプーンのデザインに差し替え。元画像（`/Users/nao/Desktop/icon.png`）も同様にプレビュー用の角丸＋黒背景が焼き込まれていた。
- 【不具合修正】最初は前回同様「各辺225pxクロップ→180x180にリサイズ」で対応したが、これは四隅の黒を消すために外周全体を均等に切り詰める方式のため、実際には黒くない上下左右の中央部分まで一緒にクロップされてしまい、画像全体が不必要に拡大（ズーム）されて構図の一部（虫眼鏡の柄など）が見切れる結果になった。
  - 修正: クロップではなく「行単位の黒つぶし」に変更。各行を左右から走査し、黒（RGB各値が閾値25以下）が続く区間だけをその内側の色で塗り替える方式にした。角の黒い部分だけを周囲の色で置き換え、黒くない中央部分は一切削らないため、ズームやトリミングなしで元の構図をそのまま180x180に縮小できる。
  - この処理はこのアイコン特有の「四隅だけが黒い正方形画像」という前提に依存するため、汎用スクリプト化はせず都度Pythonワンライナーで実行している。

## 主要機能

### 検索フィルタ（`src/components/SearchFilter.tsx`）

- キーワード（フリーテキスト）
- 「駅名・エリア」入力欄と「現在地を使う」ボタンは排他（現在地取得時はエリア欄をクリア、逆に手入力すると現在地情報は保持されるが検索時はplace優先ではなくcurrent_lat/lngが入っていればそちらが使われる）
- ジャンル選択（和食・洋食・イタリアン・中華・ラーメン・居酒屋・焼肉・カフェ・バー・韓国料理・指定なし）
- 距離スライダー: 100m〜2000m、100m刻み、デフォルト500m
- 予算上限セレクト（〜1,000/2,000/3,000/5,000/10,000円 / 指定なし）※現状バックエンドの絞り込みには使われていない（後述）
- 最低評価セレクト（★3.0/3.5/4.0/4.5以上 / 指定なし）
- モバイルでは「絞り込み」ヘッダーをタップして開閉、検索実行時に自動で閉じる

### 検索API（`GET /api/search`、フロントは `src/app/api/search/route.ts` でバックエンドへプロキシ）

パラメータ: `keyword` / `place` / `genre` / `budget_max` / `rating_min` / `radius` / `current_lat` / `current_lng`

バックエンド (`backend/app/api/search.py`) の検索ロジック:

1. **位置決定**: `current_lat`/`current_lng` があればそれを使用。なければ `place` を `"{place}駅"` でText Search 1件だけ叩いてジオコーディング（`_geocode_station`）。
2. **検索半径**: 指定が無い場合は500m。現在地検索で `radius` 未指定なら1000m。
3. **検索モード分岐**（`genre`・`keyword` が両方空かどうかで分岐）:
   - **ジャンル・キーワードなし（エリア検索）**:
     - 現在地: Nearby Search 1ページ（`includedTypes=[restaurant, cafe, bar]`, `rankPreference=POPULARITY`）。0件ならText Search「高評価 グルメ」にフォールバック。
     - 駅名・エリア指定: Text Search「{place} 高評価 グルメ」(60件) と Text Search「{place} 焼肉」(20件、焼肉店の取りこぼし補完用) を実行し `id` で重複排除しつつマージ。両方0件ならText Search「{place} グルメ」にフォールバック。
   - **ジャンル・キーワードあり**: Text Search「{place} {genre} {keyword}」（すべて空なら`"飲食店"`）。0件かつ位置情報があればNearby Searchにフォールバック。
4. **絞り込み**: Haversine距離計算で `effective_radius` 以内のみ残す（`distance_m` をセット）。`rating_min` 指定時はその評価未満を除外。
5. **並び替え**: 評価（`rating`）降順、最大60件（`SEARCH_RESULT_LIMIT`）。

Google Places API呼び出し（`backend/app/crawlers/google_places.py`）:

- Text Search / Nearby Search とも1ページ20件、`pageToken` で最大3ページまで追加取得可能（`search_restaurants` の `max_pages` は `count` から算出、現在の呼び出しは基本1ページ運用）。
- レスポンスは `PLACE_FIELD_MASK`（id, displayName, formattedAddress, rating, userRatingCount, location, primaryType, primaryTypeDisplayName, googleMapsUri）のみ取得し、写真フィールドは取得していない（API課金を抑える意図）。
- `primaryType` を `TYPE_MAP`（約35種類）で日本語ジャンル名に変換。

### 検索結果カード（`src/components/RestaurantCard.tsx`）

- 店舗写真は取得していないため、ジャンルにマッチする9パターンの生成画像（`public/genre-images/*.png`: 焼肉・居酒屋・カフェ・ラーメン・寿司・イタリアン・中華・和食・バー、マッチしなければ `restaurant.png`）を表示。
- 評価バッジをクリックすると、`place_id` から組み立てたGoogle検索の口コミページ（`https://search.google.com/local/reviews?placeid=...`）を新規タブで開く。
- 「店舗詳細を見る」リンクは `googleMapsUri`（Google Maps）へ。
- 距離は1km未満は `m`、以上は小数1桁の `km` で表示。

## データモデル（`backend/app/models/restaurant.py`）

```python
class Restaurant(BaseModel):
    id: str
    name: str
    address: str
    station: Optional[str] = None        # 未設定（常にnull）
    genre: list[str] = []
    rating: Optional[float] = None
    review_count: Optional[int] = None
    budget_min: Optional[int] = None      # 未設定（常にnull）
    budget_max: Optional[int] = None      # 未設定（常にnull）
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None       # 未設定（常にnull）
    url: Optional[str] = None
    source: str                           # 常に "google"
    distance_m: Optional[int] = None
```

## 既知の制約・未実装事項

- **予算フィルタは実質未使用**: `budget_max` はAPIパラメータとして受け取るが、`Restaurant.budget_min/budget_max` がGoogle Places APIレスポンスから設定されていないため、絞り込み処理（`search.py`）でも使われていない。UIの予算セレクトは選択できるが結果には反映されない。
- **`station` / `photo_url` は常にnull**: カード表示は `station ?? address` でaddressにフォールバックしている。
- **`HOTPEPPER_API_KEY`** は `.env.example` に残るが未使用（Google Places単独運用）。
- **認証は単一共有パスワード方式**: ユーザー個別のアカウント管理は無い。
