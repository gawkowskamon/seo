"""
Article Import Service
Import articles from URL (scrape) or WordPress REST API, then optimize with AI.
"""

import json
import re
import logging
import httpx
from bs4 import BeautifulSoup
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

OPTIMIZE_PROMPT = """Przeanalizuj ponizszy artykul i zoptymalizuj go pod SEO.

Tytul: {title}
Tresc (HTML): {content}

Zwroc WYLACZNIE JSON (bez markdown):
{{
  "title": "Zoptymalizowany tytul (50-60 znakow, ze slowem kluczowym)",
  "slug": "tytul-slug-bez-polskich-znakow",
  "meta_title": "Meta tytul SEO (max 60 znakow)",
  "meta_description": "Meta opis SEO (120-160 znakow)",
  "primary_keyword": "wykryte glowne slowo kluczowe",
  "secondary_keywords": ["slowo1", "slowo2", "slowo3"],
  "sections": [
    {{
      "heading": "Naglowek H2",
      "anchor": "naglowek-slug",
      "content": "<p>Tresc sekcji w HTML</p>",
      "subsections": [
        {{
          "heading": "Naglowek H3",
          "anchor": "podnaglowek-slug",
          "content": "<p>Tresc podsekcji</p>"
        }}
      ]
    }}
  ],
  "faq": [
    {{"question": "Pytanie FAQ", "answer": "Odpowiedz"}}
  ],
  "toc": [
    {{"label": "Nazwa sekcji", "anchor": "anchor-slug"}}
  ],
  "sources": [],
  "internal_link_suggestions": [],
  "seo_suggestions": [
    "Konkretna sugestia poprawy SEO artykulu"
  ]
}}"""


async def scrape_article_from_url(url: str) -> dict:
    """Scrape article content from a URL."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()
        
        # Try to find article content
        article = soup.find("article") or soup.find("main") or soup.find(class_=re.compile(r"post|article|content|entry"))
        
        if article:
            content_html = str(article)
        else:
            body = soup.find("body")
            content_html = str(body) if body else str(soup)
        
        # Get title
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        elif soup.find("title"):
            title = soup.find("title").get_text(strip=True)
        
        # Get meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")
        
        # Clean content
        clean_soup = BeautifulSoup(content_html, "html.parser")
        text_content = clean_soup.get_text(separator="\n", strip=True)
        
        return {
            "title": title,
            "content_html": content_html[:15000],
            "text_content": text_content[:10000],
            "meta_description": meta_desc,
            "source_url": url,
            "word_count": len(text_content.split())
        }


async def import_from_wordpress(wp_url: str, wp_user: str = None, wp_password: str = None, limit: int = 20) -> list:
    """Import articles from WordPress REST API."""
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    params = {"per_page": limit, "status": "publish", "_fields": "id,title,content,excerpt,slug,date,link"}
    
    headers = {}
    if wp_user and wp_password:
        import base64
        creds = base64.b64encode(f"{wp_user}:{wp_password}".encode()).decode()
        headers["Authorization"] = f"Basic {creds}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        
        posts = response.json()
        articles = []
        for post in posts:
            articles.append({
                "wp_id": post.get("id"),
                "title": post.get("title", {}).get("rendered", ""),
                "content_html": post.get("content", {}).get("rendered", ""),
                "excerpt": post.get("excerpt", {}).get("rendered", ""),
                "slug": post.get("slug", ""),
                "date": post.get("date", ""),
                "source_url": post.get("link", ""),
                "word_count": len(BeautifulSoup(post.get("content", {}).get("rendered", ""), "html.parser").get_text().split())
            })
        
        return articles


async def optimize_imported_article(title: str, content_html: str, emergent_key: str) -> dict:
    """Use AI to optimize an imported article for SEO."""
    # Truncate content to fit in context
    content_truncated = content_html[:8000]
    
    prompt = OPTIMIZE_PROMPT.format(title=title, content=content_truncated)
    
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"import-optimize",
        system_message="Jestes ekspertem SEO. Optymalizujesz artykuly pod wyszukiwarki. Odpowiadaj WYLACZNIE JSON-em."
    )
    chat.with_model("openai", "gpt-4.1-mini")
    
    response = await chat.send_async(UserMessage(text=prompt))
    
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    
    result = json.loads(text)
    return result
