import asyncio
import httpx
from app.models.restaurant import Restaurant

PLACES_V1 = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.location",
    "places.photos",
    "places.currentOpeningHours",
    "places.primaryType",
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
        open_now = (
            p.get("currentOpeningHours", {}).get("openNow")
            if "currentOpeningHours" in p else None
        )
        results.append(Restaurant(
            id=f"google_{place_id}",
            name=p.get("displayName", {}).get("text", ""),
            address=p.get("formattedAddress", ""),
            rating=p.get("rating"),
            review_count=p.get("userRatingCount"),
            lat=loc.get("latitude"),
            lng=loc.get("longitude"),
            photo_url=photo_url,
            url=p.get("googleMapsUri"),
            source="google",
            open_now=open_now,
        ))
    return results

async def search_restaurants(
    query: str,
    api_key: str,
    location: str = "",
    radius: int = 1500,
    count: int = 60,
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

    base_body: dict = {
        "textQuery": effective_query,
        "languageCode": "ja",
        "maxResultCount": 20,
    }
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
