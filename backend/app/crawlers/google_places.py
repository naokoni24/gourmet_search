import asyncio
import httpx
from app.models.restaurant import Restaurant

TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

# "restaurant" は Google の親カテゴリ（焼肉・ラーメン・寿司等すべてを含む）
ALL_FOOD_TYPES = ["restaurant", "cafe", "bar"]

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

PLACE_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.location",
    "places.primaryType",
    "places.primaryTypeDisplayName",
    "places.googleMapsUri",
])

TEXT_FIELD_MASK = ",".join([
    PLACE_FIELD_MASK,
    "nextPageToken",
])

def _parse_places(data: dict, _api_key: str) -> list[Restaurant]:
    results = []
    for p in data.get("places", []):
        place_id = p.get("id", "")
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
            photo_url=None,
            url=p.get("googleMapsUri"),
            source="google",
        ))
    return results

async def _nearby_one_group(
    client: httpx.AsyncClient, api_key: str,
    location: str, radius: int, included_types: list[str], max_pages: int,
) -> list[Restaurant]:
    """Nearby Search（1ページ20件、最大3ページ）"""
    lat, lng = location.split(",")
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": PLACE_FIELD_MASK,
        "Accept-Language": "ja",
    }
    base_body: dict = {
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
    results: list[Restaurant] = []
    page_token: str | None = None
    for _ in range(max_pages):
        body = {**base_body}
        if page_token:
            body["pageToken"] = page_token
        res = await client.post(NEARBY_SEARCH_URL, json=body, headers=headers)
        if res.status_code != 200:
            print(f"[nearby_search] HTTP {res.status_code}: {res.text[:500]}")
            break
        data = res.json()
        if "error" in data:
            print(f"[nearby_search] API error: {data['error']}")
            break
        results.extend(_parse_places(data, api_key))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
        await asyncio.sleep(2)
    return results

async def search_nearby(
    api_key: str, location: str, radius: int,
    included_types: list[str] | None = None,
    max_pages: int = 3,
) -> list[Restaurant]:
    """Nearby Search で周辺の飲食店を取得（最大60件）"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await _nearby_one_group(
            client, api_key, location, radius,
            included_types or ALL_FOOD_TYPES,
            max_pages=max(1, min(max_pages, 3)),
        )

async def search_restaurants(
    query: str,
    api_key: str,
    location: str = "",
    radius: int = 1500,
    count: int = 60,
) -> list[Restaurant]:
    """Text Search（全ケース共通）"""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": TEXT_FIELD_MASK,
        "Accept-Language": "ja",
    }

    base_body: dict = {
        "textQuery": query,
        "languageCode": "ja",
        "maxResultCount": 20,
    }
    if location:
        lat, lng = location.split(",")
        # locationBiasは強制ではなくGoogle側の重み付けだが、ここを実際の距離より
        # 広く取ると圏外の店舗が上位互換枠を消費し、後段のdistance_mフィルタで
        # 落とされる無駄が増える（＝本来表示されるべき近場の店舗が漏れる）ため、
        # ユーザーが指定した距離をそのまま使う
        api_radius = radius
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
            if res.status_code != 200:
                print(f"[text_search] HTTP {res.status_code}: {res.text[:500]}")
                break
            data = res.json()
            if "error" in data:
                print(f"[text_search] API error: {data['error']}")
                break
            results.extend(_parse_places(data, api_key))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            await asyncio.sleep(2)

    return results
