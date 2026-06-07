from pydantic import BaseModel
from typing import Optional

class Restaurant(BaseModel):
    id: str
    name: str
    address: str
    station: Optional[str] = None
    genre: list[str] = []
    rating: Optional[float] = None
    review_count: Optional[int] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    photo_url: Optional[str] = None
    url: Optional[str] = None
    source: str  # 'google' | 'hotpepper'
    open_now: Optional[bool] = None

class SearchParams(BaseModel):
    keyword: str = ""
    area: str = ""
    station: str = ""
    genre: str = ""
    budget_max: Optional[int] = None
    rating_min: Optional[float] = None
    open_now: bool = False
    sources: list[str] = ["google", "hotpepper", "blog"]
