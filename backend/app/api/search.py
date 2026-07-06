from fastapi import APIRouter, Query
from typing import Optional
import os
import math

from app.models.restaurant import Restaurant
from app.crawlers import google_places

router = APIRouter()

AREA_PRIMARY_COUNT = 60
AREA_SUPPLEMENT_COUNT = 20
SEARCH_RESULT_LIMIT = 60

# フロントの絞り込みモーダル（GENRES）と同じジャンル名一覧。
# キーワード欄にこれらとまったく同じ文字列が入力された場合も、
# ジャンル選択時と同様に厳密フィルタの対象にする。
GENRE_LABELS = {"和食", "洋食", "イタリアン", "中華", "ラーメン", "居酒屋", "焼肉", "カフェ", "バー", "韓国料理"}

# UIの「ジャンル」は大まかな括りだが、Googleの primaryType（TYPE_MAP参照）は
# もっと細かく分かれているため、厳密フィルタで完全一致だけを見ると
# 例えば「洋食」で検索した際に「ビストロ」「ステーキ」「フレンチ」等の
# 実質同じ括りの店舗まで弾かれてしまう。選んだジャンルごとに許容する
# Google側の表記もあわせて定義する（未定義のジャンルは自分自身のみ許容）。
#「レストラン」はGoogleがより具体的な分類を持たない店舗（沖縄料理店等、
# 洋食と無関係な業態も含む）に広く使う汎用ラベルのため、いずれのグループにも含めない。
GENRE_GROUPS: dict[str, set[str]] = {
    "洋食": {"洋食", "ビストロ", "ステーキ", "フレンチ", "アメリカン", "ハンバーガー", "ピザ"},
    "和食": {"和食", "とんかつ", "天ぷら", "しゃぶしゃぶ", "すき焼き", "沖縄料理"},
    "居酒屋": {"居酒屋", "焼き鳥"},
    "イタリアン": {"イタリアン", "ピザ"},
}

def _genre_matches(selected_genre: str, item_genres: list[str]) -> bool:
    accepted = GENRE_GROUPS.get(selected_genre, {selected_genre})
    return any(label in g for label in accepted for g in item_genres)

def _merge_unique(*groups: list[Restaurant]) -> list[Restaurant]:
    seen: set[str] = set()
    merged: list[Restaurant] = []
    for group in groups:
        for restaurant in group:
            if restaurant.id in seen:
                continue
            seen.add(restaurant.id)
            merged.append(restaurant)
    return merged

async def _geocode_station(station: str, api_key: str) -> Optional[str]:
    import httpx
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.location",
        }
        body = {"textQuery": f"{station}駅", "languageCode": "ja", "maxResultCount": 1}
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                json=body, headers=headers
            )
            data = res.json()
        places = data.get("places", [])
        if places:
            loc = places[0].get("location", {})
            return f"{loc['latitude']},{loc['longitude']}"
    except Exception:
        pass
    return None

@router.get("/search")
async def search(
    keyword: str = Query("", description="キーワード"),
    place: str = Query("", description="駅名・エリア（例：阿佐ヶ谷、渋谷）"),
    genre: str = Query("", description="ジャンル（例：ラーメン）"),
    budget_max: Optional[int] = Query(None, description="予算上限"),
    rating_min: Optional[float] = Query(None, description="最低評価"),
    radius: Optional[int] = Query(None, description="駅からの距離(m)"),
    current_lat: Optional[float] = Query(None, description="現在地緯度"),
    current_lng: Optional[float] = Query(None, description="現在地経度"),
):
    google_key = os.getenv("GOOGLE_PLACES_API_KEY", "")

    location = None
    if current_lat is not None and current_lng is not None:
        location = f"{current_lat},{current_lng}"
    elif place and google_key:
        location = await _geocode_station(place, google_key)

    effective_radius = radius or 500
    if current_lat is not None and radius is None:
        effective_radius = 1000

    results: list[Restaurant] = []
    if google_key:
        try:
            if location and not genre and not keyword:
                # 通常のエリア検索はText Search 1ページ中心にして、API回数を抑える。
                if place:
                    high_rating_results = await google_places.search_restaurants(
                        f"{place} 高評価 グルメ",
                        google_key, count=AREA_PRIMARY_COUNT,
                        location=location,
                        radius=effective_radius,
                    )
                    print(f"[high rating search] {len(high_rating_results)} results for {place} r={effective_radius}")
                    yakiniku_results = await google_places.search_restaurants(
                        f"{place} 焼肉",
                        google_key, count=AREA_SUPPLEMENT_COUNT,
                        location=location,
                        radius=effective_radius,
                    )
                    print(f"[yakiniku supplement] {len(yakiniku_results)} results for {place} r={effective_radius}")

                    results = _merge_unique(high_rating_results, yakiniku_results)
                    if not results:
                        results = await google_places.search_restaurants(
                            f"{place} グルメ",
                            google_key, count=AREA_PRIMARY_COUNT,
                            location=location,
                            radius=effective_radius,
                        )
                        print(f"[text fallback] {len(results)} results for {place} r={effective_radius}")
                else:
                    results = await google_places.search_nearby(
                        google_key, location, radius=effective_radius,
                        max_pages=1,
                    )
                    print(f"[nearby] {len(results)} results for current_loc r={effective_radius}")
                    if not results:
                        results = await google_places.search_restaurants(
                            "高評価 グルメ", google_key, count=AREA_PRIMARY_COUNT,
                            location=location,
                            radius=effective_radius,
                        )
            else:
                # ジャンル・キーワードあり → Text Search 1ページ
                query = f"{place} {genre} {keyword}".strip() or "飲食店"
                results = await google_places.search_restaurants(
                    query, google_key, count=SEARCH_RESULT_LIMIT,
                    location=location or "",
                    radius=effective_radius,
                )
                if not results and location:
                    results = await google_places.search_nearby(
                        location=location,
                        radius=effective_radius,
                        api_key=google_key,
                        max_pages=1,
                    )
                if "和食" in (genre.strip(), keyword.strip()):
                    # 「和食」はメインクエリだけだと沖縄料理店が候補に上がらないことが
                    # あるため、焼肉検索と同様に補完クエリでマージする
                    okinawa_results = await google_places.search_restaurants(
                        f"{place} 沖縄料理", google_key, count=AREA_SUPPLEMENT_COUNT,
                        location=location or "",
                        radius=effective_radius,
                    )
                    results = _merge_unique(results, okinawa_results)
        except Exception as e:
            import traceback
            print(f"[search error] {e}")
            traceback.print_exc()
            results = []

    def make_dist_fn(loc: str):
        lat0, lng0 = map(float, loc.split(","))
        def dist_m(r: Restaurant) -> float:
            if r.lat is None or r.lng is None:
                return float('inf')
            dlat = math.radians(r.lat - lat0)
            dlng = math.radians(r.lng - lng0)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat0)) * math.cos(math.radians(r.lat)) * math.sin(dlng/2)**2
            return 6371000 * 2 * math.asin(math.sqrt(a))
        return dist_m

    dist_fn = make_dist_fn(location) if location else None

    def filter_list(items: list[Restaurant]) -> list[Restaurant]:
        if dist_fn and effective_radius:
            items = [r for r in items if dist_fn(r) <= effective_radius]
        if rating_min is not None:
            items = [r for r in items if r.rating and r.rating >= rating_min]
        # ジャンルはテキスト検索のクエリにも使うが、Googleの分類上ジャンル名と
        # 完全一致しない店舗が混ざるため、実際のgenreフィールドでも絞り込む。
        # キーワード欄にジャンル名そのものが入力された場合も同様に扱う。
        genre_filters = {g for g in (genre.strip(), keyword.strip()) if g in GENRE_LABELS}
        for genre_filter in genre_filters:
            items = [r for r in items if _genre_matches(genre_filter, r.genre)]
        if dist_fn:
            for r in items:
                r.distance_m = round(dist_fn(r))
        return items

    restaurants = sorted(
        filter_list(results),
        key=lambda r: r.rating or 0, reverse=True
    )[:SEARCH_RESULT_LIMIT]

    return {
        "restaurants": restaurants,
        "total": len(restaurants),
    }
