"""
Export Service - Generate formatted content for Facebook, Google Business, HTML, and PDF.
"""

import re
import io
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


def strip_html(html: str) -> str:
    """Strip HTML tags and return plain text."""
    return re.sub(r'<[^>]+>', '', html).strip()


def generate_facebook_post(article: dict) -> str:
    """Generate Facebook-optimized post from article."""
    title = article.get("title", "")
    meta_desc = article.get("meta_description", "")
    
    # Get first section content as intro
    sections = article.get("sections", [])
    intro = ""
    if sections:
        intro = strip_html(sections[0].get("content", ""))
        # Limit to ~200 chars
        if len(intro) > 200:
            intro = intro[:197] + "..."
    
    # Get key points from headings
    key_points = []
    for s in sections[:4]:
        key_points.append(f"\u2714\ufe0f {s.get('heading', '')}")
    
    # FAQ teaser
    faq = article.get("faq", [])
    faq_teaser = ""
    if faq:
        faq_teaser = f"\n\n\u2753 {faq[0].get('question', '')}"
    
    post = f"""\U0001f4ca {title}

{intro}

{chr(10).join(key_points)}{faq_teaser}

\U0001f449 Przeczytaj cały artykuł na naszym blogu!

#księgowość #podatki #rachunkowość #biznes #firma #VAT #PIT #CIT"""
    
    return post


def generate_google_business_post(article: dict) -> str:
    """Generate Google Business Profile optimized post."""
    title = article.get("title", "")
    meta_desc = article.get("meta_description", "")
    
    # Google Business posts have ~1500 char limit, keep it concise
    sections = article.get("sections", [])
    intro = ""
    if sections:
        intro = strip_html(sections[0].get("content", ""))
        if len(intro) > 300:
            intro = intro[:297] + "..."
    
    post = f"""{title}

{intro}

{meta_desc}

\u260e\ufe0f Potrzebujesz pomocy z księgowością? Skontaktuj się z nami!
\U0001f449 Przeczytaj więcej na naszym blogu."""
    
    return post


def generate_full_html(article: dict) -> str:
    """Generate complete standalone HTML document from article."""
    title = article.get("title", "")
    meta_title = article.get("meta_title", title)
    meta_desc = article.get("meta_description", "")
    
    # Build TOC HTML
    toc_html = '<nav class="toc"><h2>Spis treści</h2><ol>'
    for item in article.get("toc", []):
        toc_html += f'<li><a href="#{item["anchor"]}">{item["label"]}</a></li>'
    toc_html += '</ol></nav>'
    
    # Build sections HTML
    sections_html = ""
    for section in article.get("sections", []):
        sections_html += f'<section id="{section["anchor"]}">'
        sections_html += f'<h2>{section["heading"]}</h2>'
        sections_html += section.get("content", "")
        for sub in section.get("subsections", []):
            sections_html += f'<h3 id="{sub["anchor"]}">{sub["heading"]}</h3>'
            sections_html += sub.get("content", "")
        sections_html += '</section>'
    
    # Build FAQ HTML with Schema.org markup
    faq_html = '<section class="faq"><h2>Najczęściej zadawane pytania (FAQ)</h2>'
    faq_html += '<div itemscope itemtype="https://schema.org/FAQPage">'
    for faq in article.get("faq", []):
        faq_html += f'''<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
            <h3 itemprop="name">{faq["question"]}</h3>
            <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
                <p itemprop="text">{faq["answer"]}</p>
            </div>
        </div>'''
    faq_html += '</div></section>'
    
    # Build sources HTML
    sources_html = '<section class="sources"><h2>Źródła</h2><ul>'
    for src in article.get("sources", []):
        sources_html += f'<li><a href="{src["url"]}" target="_blank" rel="noopener">{src["name"]}</a> ({src.get("type", "")})</li>'
    sources_html += '</ul></section>'
    
    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_desc}">
    <title>{meta_title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.8; max-width: 800px; margin: 0 auto; padding: 20px; color: #1a1a2e; }}
        h1 {{ color: #0a4c7a; font-size: 2em; margin-bottom: 0.5em; }}
        h2 {{ color: #0e6ba8; font-size: 1.5em; margin-top: 2em; padding-bottom: 0.3em; border-bottom: 2px solid #e8f1f8; }}
        h3 {{ color: #1a7bc0; font-size: 1.2em; }}
        .toc {{ background: #f0f7ff; padding: 20px 30px; border-radius: 8px; margin: 20px 0; }}
        .toc h2 {{ margin-top: 0; border: none; font-size: 1.3em; }}
        .toc ol {{ padding-left: 20px; }}
        .toc a {{ color: #0e6ba8; text-decoration: none; }}
        .toc a:hover {{ text-decoration: underline; }}
        .faq {{ background: #f8fafb; padding: 20px; border-radius: 8px; margin-top: 2em; }}
        .faq h3 {{ color: #0a4c7a; }}
        .sources {{ margin-top: 2em; padding-top: 1em; border-top: 2px solid #e8f1f8; }}
        .sources a {{ color: #0e6ba8; }}
        a {{ color: #0e6ba8; }}
        p {{ margin-bottom: 1em; }}
        ul, ol {{ margin-bottom: 1em; }}
        strong {{ color: #0a4c7a; }}
    </style>
</head>
<body>
    <article>
        <h1>{title}</h1>
        {toc_html}
        {sections_html}
        {faq_html}
        {sources_html}
    </article>
</body>
</html>"""
    
    return html


def generate_pdf_bytes(article: dict) -> bytes:
    """Generate PDF from article. Returns PDF bytes."""
    # Register Polish-compatible fonts
    FONT_PATH = '/usr/share/fonts/truetype/dejavu/'
    pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles with DejaVuSans (supports Polish diacritics)
    title_style = ParagraphStyle(
        'ArticleTitle',
        parent=styles['Title'],
        fontName='DejaVuSans-Bold',
        fontSize=20,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='DejaVuSans-Bold',
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor='#0e6ba8'
    )
    
    h3_style = ParagraphStyle(
        'H3Style',
        parent=styles['Heading3'],
        fontName='DejaVuSans-Bold',
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        textColor='#1a7bc0'
    )
    
    body_style = ParagraphStyle(
        'BodyText2',
        parent=styles['BodyText'],
        fontName='DejaVuSans',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    faq_q_style = ParagraphStyle(
        'FAQQuestion',
        parent=styles['Heading4'],
        fontName='DejaVuSans-Bold',
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        textColor='#0a4c7a'
    )
    
    elements = []
    
    # Title
    title = article.get("title", "Artykuł")
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))
    
    # Sections
    for section in article.get("sections", []):
        elements.append(Paragraph(section.get("heading", ""), h2_style))
        
        content = strip_html(section.get("content", ""))
        # Split into paragraphs
        for para in content.split("\n"):
            para = para.strip()
            if para:
                try:
                    elements.append(Paragraph(para, body_style))
                except Exception:
                    elements.append(Paragraph(re.sub(r'[<>&]', '', para), body_style))
        
        for sub in section.get("subsections", []):
            elements.append(Paragraph(sub.get("heading", ""), h3_style))
            sub_content = strip_html(sub.get("content", ""))
            for para in sub_content.split("\n"):
                para = para.strip()
                if para:
                    try:
                        elements.append(Paragraph(para, body_style))
                    except Exception:
                        elements.append(Paragraph(re.sub(r'[<>&]', '', para), body_style))
    
    # FAQ
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Najczesciej zadawane pytania (FAQ)", h2_style))
    for faq in article.get("faq", []):
        elements.append(Paragraph(faq.get("question", ""), faq_q_style))
        try:
            elements.append(Paragraph(faq.get("answer", ""), body_style))
        except Exception:
            elements.append(Paragraph(re.sub(r'[<>&]', '', faq.get("answer", "")), body_style))
    
    # Sources
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Zrodla", h2_style))
    for src in article.get("sources", []):
        try:
            elements.append(Paragraph(f"- {src.get('name', '')} ({src.get('url', '')})", body_style))
        except Exception:
            elements.append(Paragraph(f"- {src.get('name', '')}", body_style))
    
    doc.build(elements)
    return buffer.getvalue()
