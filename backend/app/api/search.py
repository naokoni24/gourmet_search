from fastapi import APIRouter, Query
from typing import Optional
import os
import math
import httpx

from app.models.restaurant import Restaurant, SearchParams
from app.crawlers import google_places

router = APIRouter()

async def _geocode_station(station: str, api_key: str) -> Optional[str]:
    """駅名 → "lat,lng" 文字列に変換（Places API Text Search を利用）"""
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
    open_now: bool = Query(False, description="今すぐ営業中"),
):
    query = f"{station} {area} {genre} {keyword}".strip()
    google_key = os.getenv("GOOGLE_PLACES_API_KEY", "")

    # 現在地が指定されている場合はそのまま使用、駅名の場合はジオコーディング
    location = None
    if current_lat is not None and current_lng is not None:
        location = f"{current_lat},{current_lng}"
    elif station and google_key:
        location = await _geocode_station(station, google_key)

    # 現在地検索時は radius 未指定でも 1000m をデフォルトに
    effective_radius = radius
    if current_lat is not None and effective_radius is None:
        effective_radius = 1000

    results: list[Restaurant] = []
    if google_key:
        try:
            results = await google_places.search_restaurants(
                query, google_key, count=60,
                location=location or "",
                radius=effective_radius or 1500,
                keyword=keyword,
                genre=genre,
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
        if open_now:
            items = [r for r in items if r.open_now is True]
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
        "debug": {
            "location": location,
            "effective_radius": effective_radius,
            "current_lat": current_lat,
            "current_lng": current_lng,
            "station": station,
        },
    }
