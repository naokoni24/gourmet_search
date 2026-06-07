import httpx
from app.models.restaurant import Restaurant

HOTPEPPER_BASE = "https://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

GENRE_MAP = {
    "居酒屋": "G001", "ダイニングバー": "G002", "創作料理": "G003",
    "和食": "G004", "洋食": "G005", "イタリアン": "G006", "中華": "G007",
    "焼肉": "G008", "韓国料理": "G017", "アジア・エスニック": "G009",
    "各国料理": "G010", "カラオケ": "G011", "バー": "G012",
    "ラーメン": "G013", "お好み焼き": "G016", "カフェ": "G014",
}

# ホットペッパーの range コード（m → code）
def _radius_to_range(radius_m: int) -> int:
    if radius_m <= 300:  return 1
    if radius_m <= 500:  return 2
    if radius_m <= 1000: return 3
    if radius_m <= 2000: return 4
    return 5  # 3000m

def _parse_shop(s: dict) -> Restaurant:
    lat = float(s.get("lat") or 0) or None
    lng = float(s.get("lng") or 0) or None
    return Restaurant(
        id=f"hotpepper_{s['id']}",
        name=s.get("name", ""),
        address=s.get("address", ""),
        station=s.get("station_name"),
        genre=[s.get("genre", {}).get("name", "")],
        lat=lat,
        lng=lng,
        photo_url=s.get("photo", {}).get("pc", {}).get("l"),
        url=s.get("urls", {}).get("pc"),
        source="hotpepper",
        open_now=None,
    )

async def search_restaurants(
    keyword: str,
    api_key: str,
    area: str = "",
    station: str = "",
    genre: str = "",
    location: str = "",   # "lat,lng" 形式
    radius: int = 1000,
    count: int = 300,
) -> list[Restaurant]:

    base_params: dict = {
        "key": api_key,
        "format": "json",
        "count": 100,
    }

    if genre and genre in GENRE_MAP:
        base_params["genre"] = GENRE_MAP[genre]

    # 位置情報がある場合は lat/lng + range で検索（精度高）
    if location:
        lat, lng = location.split(",")
        base_params["lat"] = lat
        base_params["lng"] = lng
        base_params["range"] = _radius_to_range(radius)
        if keyword:
            base_params["keyword"] = keyword
    else:
        # フォールバック: キーワード検索
        effective_keyword = keyword or station or area or "レストラン"
        base_params["keyword"] = f"{station} {effective_keyword}".strip() if station else effective_keyword
        if area:
            base_params["address"] = area

    results: list[Restaurant] = []
    max_pages = min((count + 99) // 100, 10)

    async with httpx.AsyncClient(timeout=10.0) as client:
        for page in range(max_pages):
            params = {**base_params, "start": page * 100 + 1}
            res = await client.get(HOTPEPPER_BASE, params=params)
            data = res.json().get("results", {})
            shops = data.get("shop", [])
            results.extend(_parse_shop(s) for s in shops)

            available = int(data.get("results_available", 0))
            if len(results) >= available or len(shops) < 100:
                break

    return results
