from fastapi import APIRouter, Query
from typing import Optional
import os
import math

from app.models.restaurant import Restaurant
from app.crawlers import google_places

router = APIRouter()

async def _geocode_station(station: str, api_key: str) -> Optional[str]:
    """駅名 → "lat,lng" 文字列に変換（Places API Text Search を利用）"""
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
    area: str = Query("", description="エリア（例：渋谷）"),
    station: str = Query("", description="最寄り駅（例：新宿駅）"),
    genre: str = Query("", description="ジャンル（例：ラーメン）"),
    budget_max: Optional[int] = Query(None, description="予算上限"),
    rating_min: Optional[float] = Query(None, description="最低評価"),
    radius: Optional[int] = Query(None, description="駅からの距離(m)"),
    current_lat: Optional[float] = Query(None, description="現在地緯度"),
    current_lng: Optional[float] = Query(None, description="現在地経度"),
):
    place = f"{station} {area}".strip()
    google_key = os.getenv("GOOGLE_PLACES_API_KEY", "")

    location = None
    if current_lat is not None and current_lng is not None:
        location = f"{current_lat},{current_lng}"
    elif station and google_key:
        location = await _geocode_station(station, google_key)

    effective_radius = radius
    if current_lat is not None and effective_radius is None:
        effective_radius = 1000  # 現在地検索のデフォルト
    elif station and location and effective_radius is None:
        effective_radius = 1500  # 駅名検索のデフォルト

    results: list[Restaurant] = []
    if google_key:
        try:
            if (genre or keyword) or not location:
                # キーワード/ジャンル指定あり、または位置情報なし → Text Search
                query = f"{place} {genre} {keyword}".strip() or "飲食店"
                results = await google_places.search_restaurants(
                    query, google_key, count=60,
                    location=location or "",
                    radius=effective_radius or 1500,
                )
            else:
                # 位置情報あり・ジャンル未指定 → Nearby Search（全飲食店を網羅）
                results = await google_places.search_nearby(
                    google_key, location,
                    radius=effective_radius or 1500,
                )
        except Exception:
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
        if dist_fn:
            for r in items:
                r.distance_m = round(dist_fn(r))
        return items

    restaurants = sorted(
        filter_list(results),
        key=lambda r: r.rating or 0, reverse=True
    )[:60]

    return {
        "restaurants": restaurants,
        "total": len(restaurants),
    }
