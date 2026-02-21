"""
SEO Audit Service
Scrape a URL and provide AI-powered SEO recommendations.
"""

import re
import json
import logging
import httpx
from bs4 import BeautifulSoup
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

AUDIT_PROMPT = """Przeprowadz kompleksowy audyt SEO ponizszej strony.

URL: {url}
Tytul strony: {title}
Meta description: {meta_desc}
Naglowki H1: {h1s}
Naglowki H2: {h2s}
Liczba slow: {word_count}
Liczba obrazkow (z alt): {imgs_with_alt} / (bez alt): {imgs_without_alt}
Linki wewnetrzne: {internal_links}
Linki zewnetrzne: {external_links}
Czy ma SSL: {has_ssl}
Canonical URL: {canonical}
Robots meta: {robots}
Schema.org: {has_schema}
Open Graph: {has_og}

Fragment tresci (500 slow):
{content_sample}

Odpowiedz WYLACZNIE JSON-em:
{{
  "overall_score": 72,
  "grade": "B",
  "critical_issues": [
    {{
      "issue": "Opis problemu",
      "impact": "wysoki|sredni|niski",
      "recommendation": "Co zrobic"
    }}
  ],
  "on_page_seo": {{
    "score": 75,
    "findings": [
      {{"item": "Title tag", "status": "ok|warning|error", "detail": "Opis"}}
    ]
  }},
  "content_analysis": {{
    "score": 70,
    "findings": [
      {{"item": "Dlugosc tresci", "status": "ok|warning|error", "detail": "Opis"}}
    ]
  }},
  "technical_seo": {{
    "score": 65,
    "findings": [
      {{"item": "SSL", "status": "ok|warning|error", "detail": "Opis"}}
    ]
  }},
  "recommendations": [
    {{
      "priority": "wysoki|sredni|niski",
      "category": "on-page|content|technical|ux",
      "title": "Krotki tytul",
      "description": "Szczegolowy opis co zrobic",
      "estimated_impact": "Szacowany wplyw na SEO"
    }}
  ],
  "keyword_opportunities": [
    {{
      "keyword": "propozycja slowa kluczowego",
      "reason": "dlaczego warto"
    }}
  ],
  "summary": "2-3 zdania podsumowania audytu"
}}"""


async def scrape_for_audit(url: str) -> dict:
    """Scrape a URL and extract SEO-relevant data."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        meta_desc = ""
        md_tag = soup.find("meta", attrs={"name": "description"})
        if md_tag:
            meta_desc = md_tag.get("content", "")

        h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]

        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        word_count = len(text.split())

        imgs = soup.find_all("img")
        imgs_with_alt = sum(1 for img in imgs if img.get("alt", "").strip())
        imgs_without_alt = len(imgs) - imgs_with_alt

        links = soup.find_all("a", href=True)
        from urllib.parse import urlparse
        base_domain = urlparse(url).netloc
        internal = sum(1 for l in links if base_domain in (urlparse(l["href"]).netloc or base_domain))
        external = len(links) - internal

        canonical = ""
        can_tag = soup.find("link", attrs={"rel": "canonical"})
        if can_tag:
            canonical = can_tag.get("href", "")

        robots = ""
        rob_tag = soup.find("meta", attrs={"name": "robots"})
        if rob_tag:
            robots = rob_tag.get("content", "")

        has_schema = bool(soup.find("script", attrs={"type": "application/ld+json"}))
        has_og = bool(soup.find("meta", attrs={"property": re.compile(r"^og:")}))

        return {
            "url": url,
            "title": title_text,
            "meta_desc": meta_desc,
            "h1s": h1s[:5],
            "h2s": h2s[:10],
            "word_count": word_count,
            "imgs_with_alt": imgs_with_alt,
            "imgs_without_alt": imgs_without_alt,
            "internal_links": internal,
            "external_links": external,
            "has_ssl": url.startswith("https"),
            "canonical": canonical,
            "robots": robots,
            "has_schema": has_schema,
            "has_og": has_og,
            "content_sample": text[:2000]
        }


async def run_seo_audit(url: str, emergent_key: str) -> dict:
    """Run full SEO audit on a URL."""
    data = await scrape_for_audit(url)

    prompt = AUDIT_PROMPT.format(
        url=data["url"],
        title=data["title"],
        meta_desc=data["meta_desc"],
        h1s=", ".join(data["h1s"]) or "brak",
        h2s=", ".join(data["h2s"][:8]) or "brak",
        word_count=data["word_count"],
        imgs_with_alt=data["imgs_with_alt"],
        imgs_without_alt=data["imgs_without_alt"],
        internal_links=data["internal_links"],
        external_links=data["external_links"],
        has_ssl=data["has_ssl"],
        canonical=data["canonical"] or "brak",
        robots=data["robots"] or "brak",
        has_schema=data["has_schema"],
        has_og=data["has_og"],
        content_sample=data["content_sample"][:1500]
    )

    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"seo-audit-{url[:30]}",
        system_message="Jestes ekspertem SEO. Przeprowadzasz audyty stron. Odpowiadaj WYLACZNIE JSON-em."
    )
    chat.with_model("openai", "gpt-4.1-mini")

    response = await chat.send_message(UserMessage(text=prompt))
    text = response.strip() if isinstance(response, str) else str(response)
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    result = json.loads(text)
    result["scraped_data"] = {
        "title": data["title"],
        "meta_desc": data["meta_desc"],
        "word_count": data["word_count"],
        "h1_count": len(data["h1s"]),
        "h2_count": len(data["h2s"]),
        "images_total": data["imgs_with_alt"] + data["imgs_without_alt"],
        "internal_links": data["internal_links"],
        "external_links": data["external_links"]
    }
    return result
