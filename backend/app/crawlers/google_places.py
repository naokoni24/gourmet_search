import asyncio
import httpx
from app.models.restaurant import Restaurant

PLACES_V1 = "https://places.googleapis.com/v1/places:searchText"

# キーワード/ジャンル → Google includedType マッピング
KEYWORD_TO_TYPE: dict[str, str] = {
    "ラーメン": "ramen_restaurant",
    "寿司": "sushi_restaurant", "すし": "sushi_restaurant", "鮨": "sushi_restaurant",
    "焼肉": "barbecue_restaurant", "焼き肉": "barbecue_restaurant",
    "焼き鳥": "yakitori_restaurant", "やきとり": "yakitori_restaurant",
    "イタリアン": "italian_restaurant", "イタリア": "italian_restaurant",
    "中華": "chinese_restaurant", "中国料理": "chinese_restaurant",
    "韓国料理": "korean_restaurant", "韓国": "korean_restaurant",
    "カフェ": "cafe", "コーヒー": "coffee_shop",
    "居酒屋": "japanese_izakaya_restaurant",
    "和食": "japanese_restaurant",
    "とんかつ": "tonkatsu_restaurant",
    "天ぷら": "tempura_restaurant",
    "しゃぶしゃぶ": "shabu_shabu_restaurant",
    "ピザ": "pizza_restaurant",
    "ハンバーガー": "hamburger_restaurant",
    "バー": "bar",
}

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
    "vegetarian_restaurant": "ベジタリアン", "vegan_restaurant": "ビーガン",
    "noodle_restaurant": "麺料理", "yakitori_restaurant": "焼き鳥",
    "shabu_shabu_restaurant": "しゃぶしゃぶ", "sukiyaki_restaurant": "すき焼き",
    "tonkatsu_restaurant": "とんかつ", "tempura_restaurant": "天ぷら",
    "izakaya": "居酒屋", "japanese_izakaya_restaurant": "居酒屋",
    "bistro": "ビストロ", "diner": "ダイナー", "western_restaurant": "洋食",
    "cafe": "カフェ", "coffee_shop": "カフェ",
    "bar": "バー", "bakery": "ベーカリー", "dessert_shop": "デザート",
    "ice_cream_shop": "アイスクリーム", "fast_food_restaurant": "ファストフード",
    "food_court": "フードコート", "buffet_restaurant": "バイキング",
    "brunch_restaurant": "ブランチ", "breakfast_restaurant": "朝食",
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
        if primary_type in TYPE_MAP:
            genre = [TYPE_MAP[primary_type]]
        elif type_display:
            genre = [type_display]
        else:
            genre = []
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

async def search_restaurants(
    query: str,
    api_key: str,
    location: str = "",
    radius: int = 1500,
    count: int = 60,
    keyword: str = "",
    genre: str = "",
) -> list[Restaurant]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
        "Accept-Language": "ja",
    }
    food_words = ["レストラン", "飲食", "ラーメン", "寿司", "焼肉", "カフェ", "居酒屋",
                  "restaurant", "ramen", "sushi", "cafe", "food", "lunch", "dinner"]
    has_food_word = any(w in query.lower() for w in food_words)
    effective_query = query if has_food_word else f"{query} レストラン"

    # キーワード/ジャンルが特定の料理種別に対応する場合は includedType で絞り込む
    included_type: str | None = None
    for term in [keyword, genre]:
        if term and term in KEYWORD_TO_TYPE:
            included_type = KEYWORD_TO_TYPE[term]
            break

    base_body: dict = {
        "textQuery": effective_query,
        "languageCode": "ja",
        "maxResultCount": 20,
    }
    if included_type:
        base_body["includedType"] = included_type
    if location:
        lat, lng = location.split(",")
        base_body["locationBias"] = {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": float(radius),
            }
        }

    results: list[Restaurant] = []
    page_token: str | None = None
    max_pages = max(1, min((count + 19) // 20, 3))  # 最大3ページ（60件）

    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(max_pages):
            body = {**base_body}
            if page_token:
                body["pageToken"] = page_token

            res = await client.post(PLACES_V1, json=body, headers=headers)
            data = res.json()
            results.extend(_parse_places(data, api_key))

            page_token = data.get("nextPageToken")
            if not page_token:
                break
            await asyncio.sleep(2)  # nextPageToken は少し待たないと無効になる

    return results
