import asyncio
import httpx
from app.models.restaurant import Restaurant

TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

# ジャンル未指定時：2グループに分けて並列検索し漏れを防ぐ
FOOD_TYPE_GROUPS = [
    # グループA：和食・麺・カフェ系
    ["japanese_restaurant", "ramen_restaurant", "sushi_restaurant",
     "yakitori_restaurant", "tonkatsu_restaurant", "tempura_restaurant",
     "cafe", "fast_food_restaurant", "meal_takeaway"],
    # グループB：焼肉・居酒屋・洋食・その他
    ["barbecue_restaurant", "korean_restaurant", "japanese_izakaya_restaurant",
     "chinese_restaurant", "italian_restaurant", "steak_house",
     "hamburger_restaurant", "pizza_restaurant", "bar", "restaurant"],
]

TYPE_MAP = {
    "restaurant": "レストラン", "japanese_restaurant": "和食",
    "sushi_restaurant": "寿司", "ramen_restaurant": "ラーメン",
    "chinese_restaurant": "中華", "korean_restaurant": "韓国料理",
    "italian_restaurant": "イタリアン", "french_restaurant": "フレンチ",
    "american_restaurant": "アメリカン", "mexican_restaurant": "メキシカン",
    "thai_restaurant": "タイ料理", "indian_restaurant": "インド料理",
    "vietnamese_restaurant": "ベトナム料理", "mediterranean_restaurant": "地中海料理",
    "steak_house": "ステーキ", "hamburger_restaurant": "ハンバーガー",
    "pizza_restaurant": "ピザ", "seafood_restaurant": "海鮮",
    "noodle_restaurant": "麺料理", "yakitori_restaurant": "焼き鳥",
    "shabu_shabu_restaurant": "しゃぶしゃぶ", "sukiyaki_restaurant": "すき焼き",
    "tonkatsu_restaurant": "とんかつ", "tempura_restaurant": "天ぷら",
    "izakaya": "居酒屋", "japanese_izakaya_restaurant": "居酒屋",
    "bistro": "ビストロ", "western_restaurant": "洋食",
    "cafe": "カフェ", "coffee_shop": "カフェ", "bar": "バー",
    "fast_food_restaurant": "ファストフード", "meal_takeaway": "テイクアウト",
    "bakery": "ベーカリー", "dessert_shop": "デザート",
}

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.location",
    "places.photos",
    "places.primaryType",
    "places.primaryTypeDisplayName",
    "places.googleMapsUri",
    "nextPageToken",
])

def _parse_places(data: dict, api_key: str) -> list[Restaurant]:
    results = []
    for p in data.get("places", []):
        place_id = p.get("id", "")
        photos = p.get("photos", [])
        photo_url = (
            f"https://places.googleapis.com/v1/{photos[0]['name']}/media"
            f"?maxWidthPx=400&key={api_key}"
            if photos else None
        )
        loc = p.get("location", {})
        primary_type = p.get("primaryType", "")
        type_display = p.get("primaryTypeDisplayName", {}).get("text", "")
        genre = [TYPE_MAP[primary_type]] if primary_type in TYPE_MAP else ([type_display] if type_display else [])
        results.append(Restaurant(
            id=f"google_{place_id}",
            name=p.get("displayName", {}).get("text", ""),
            address=p.get("formattedAddress", ""),
            genre=genre,
            rating=p.get("rating"),
            review_count=p.get("userRatingCount"),
            lat=loc.get("latitude"),
            lng=loc.get("longitude"),
            photo_url=photo_url,
            url=p.get("googleMapsUri"),
            source="google",
        ))
    return results

async def _nearby_one_group(
    client: httpx.AsyncClient, api_key: str,
    location: str, radius: int, included_types: list[str],
) -> list[Restaurant]:
    """1グループ分のNearby Search（最大20件）"""
    lat, lng = location.split(",")
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
        "Accept-Language": "ja",
    }
    body = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "rankPreference": "POPULARITY",
        "locationRestriction": {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": float(radius),
            }
        },
    }
    res = await client.post(NEARBY_SEARCH_URL, json=body, headers=headers)
    return _parse_places(res.json(), api_key)

async def search_nearby(
    api_key: str, location: str, radius: int,
    included_types: list[str] | None = None,
) -> list[Restaurant]:
    """Nearby Search で周辺の飲食店を網羅取得"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        if included_types:
            # ジャンル指定あり：1グループで検索
            return await _nearby_one_group(client, api_key, location, radius, included_types)
        else:
            # ジャンル未指定：2グループ並列検索してマージ（漏れ防止）
            tasks = [
                _nearby_one_group(client, api_key, location, radius, group)
                for group in FOOD_TYPE_GROUPS
            ]
            batches = await asyncio.gather(*tasks, return_exceptions=True)
            seen: set[str] = set()
            results: list[Restaurant] = []
            for batch in batches:
                if isinstance(batch, list):
                    for r in batch:
                        if r.id not in seen:
                            seen.add(r.id)
                            results.append(r)
            return results

async def search_restaurants(
    query: str,
    api_key: str,
    location: str = "",
    radius: int = 1500,
    count: int = 60,
) -> list[Restaurant]:
    """キーワード・ジャンル指定時：Text Search"""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
        "Accept-Language": "ja",
    }
    food_words = ["飲食", "レストラン", "ラーメン", "寿司", "焼肉", "カフェ", "居酒屋",
                  "restaurant", "ramen", "sushi", "cafe", "food"]
    has_food_word = any(w in query.lower() for w in food_words)
    effective_query = query if has_food_word else f"{query} 飲食店"

    base_body: dict = {
        "textQuery": effective_query,
        "languageCode": "ja",
        "maxResultCount": 20,
    }
    if location:
        lat, lng = location.split(",")
        api_radius = max(radius * 1.5, 2000)
        base_body["locationBias"] = {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": api_radius,
            }
        }

    results: list[Restaurant] = []
    page_token: str | None = None
    max_pages = max(1, min((count + 19) // 20, 3))

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(max_pages):
            body = {**base_body}
            if page_token:
                body["pageToken"] = page_token
            res = await client.post(TEXT_SEARCH_URL, json=body, headers=headers)
            data = res.json()
            results.extend(_parse_places(data, api_key))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            await asyncio.sleep(2)

    return results
