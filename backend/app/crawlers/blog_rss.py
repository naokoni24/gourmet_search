import feedparser
from urllib.parse import quote
from pydantic import BaseModel
from typing import Optional
import re

class BlogPost(BaseModel):
    title: str
    url: str
    summary: str
    published: Optional[str] = None
    source_name: str

def _build_feeds(keyword: str, area: str) -> list[dict]:
    q = quote(f"{area} {keyword}".strip())
    q_area = quote(area) if area else quote(keyword)
    return [
        # はてなブックマーク キーワード検索RSS
        {
            "name": "はてなブックマーク",
            "url": f"https://b.hatena.ne.jp/search/text?q={q}+グルメ&mode=rss&sort=recent",
        },
        # にほんブログ村 グルメカテゴリ新着RSS
        {
            "name": "にほんブログ村",
            "url": f"https://blogmura.com/search/rss/?q={q}",
        },
        # はてなブログ タグ検索RSS
        {
            "name": "はてなブログ",
            "url": f"https://bookmark.hatenastaff.com/search?q={q}&mode=rss",
        },
    ]

async def search_blog_posts(keyword: str, area: str = "") -> list[BlogPost]:
    query_words = (f"{area} {keyword}".strip()).split()
    results: list[BlogPost] = []
    seen_urls: set[str] = set()

    for feed_info in _build_feeds(keyword, area):
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:15]:
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                full_text = title + summary
                # クエリワードのいずれかが含まれるもののみ
                if query_words and not any(w in full_text for w in query_words):
                    continue
                seen_urls.add(url)
                results.append(BlogPost(
                    title=title,
                    url=url,
                    summary=_clean_html(summary)[:200],
                    published=entry.get("published"),
                    source_name=feed_info["name"],
                ))
        except Exception:
            continue

    return results

def _clean_html(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)
