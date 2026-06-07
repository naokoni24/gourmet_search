from fastapi import APIRouter, Query
from typing import Optional
import os
import asyncio
import math
import httpx

from app.models.restaurant import Restaurant, SearchParams
from app.crawlers import google_places, hotpepper, blog_rss

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
    sources: str = Query("google,hotpepper,blog", description="取得ソース"),
):
    source_list = sources.split(",")
    query = f"{station} {area} {genre} {keyword}".strip()

    google_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
    hp_key = os.getenv("HOTPEPPER_API_KEY", "")

    async def empty():
        return []

    # 現在地が指定されている場合はそのまま使用、駅名の場合はジオコーディング
    location = None
    if current_lat is not None and current_lng is not None:
        location = f"{current_lat},{current_lng}"
    elif station and radius and google_key:
        location = await _geocode_station(station, google_key)

    tasks = []
    if "google" in source_list and google_key:
        tasks.append(google_places.search_restaurants(
            query, google_key, count=60,
            location=location or "",
            radius=radius or 1500,
        ))
    else:
        tasks.append(empty())

    if "hotpepper" in source_list and hp_key:
        tasks.append(hotpepper.search_restaurants(
            keyword=keyword, api_key=hp_key,
            area=area, station=station, genre=genre,
            location=location or "",
            radius=radius or 1000,
            count=300,
        ))
    else:
        tasks.append(empty())

    if "blog" in source_list:
        tasks.append(blog_rss.search_blog_posts(keyword=f"{area} {keyword}".strip(), area=area))
    else:
        tasks.append(empty())

    google_results, hp_results, blog_results = await asyncio.gather(*tasks, return_exceptions=True)

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

    dist_fn = make_dist_fn(location) if (location and radius) else None

    def filter_list(items: list[Restaurant]) -> list[Restaurant]:
        if dist_fn and radius:
            items = [r for r in items if dist_fn(r) <= radius]
        if rating_min is not None:
            items = [r for r in items if r.rating and r.rating >= rating_min]
        if open_now:
            items = [r for r in items if r.open_now is True]
        return items

    google_list = sorted(
        filter_list(google_results if isinstance(google_results, list) else []),
        key=lambda r: r.rating or 0, reverse=True
    )[:60]

    hp_list = filter_list(hp_results if isinstance(hp_results, list) else [])

    # Google(評価順60件) + Hotpepper を評価順でマージ
    restaurants: list[Restaurant] = sorted(
        google_list + hp_list,
        key=lambda r: r.rating or 0, reverse=True
    )

    blogs = blog_results if isinstance(blog_results, list) else []

    return {
        "restaurants": restaurants,
        "blogs": blogs,
        "total": len(restaurants),
    }
