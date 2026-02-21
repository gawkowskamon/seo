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
        toc_html += f'<li><a href="#{item.get("anchor", "")}">{item.get("label", item.get("title", ""))}</a></li>'
    toc_html += '</ol></nav>'
    
    # Build sections HTML
    sections_html = ""
    for section in article.get("sections", []):
        sections_html += f'<section id="{section.get("anchor", "")}">'
        sections_html += f'<h2>{section.get("heading", "")}</h2>'
        sections_html += section.get("content", "")
        for sub in section.get("subsections", []):
            sections_html += f'<h3 id="{sub.get("anchor", "")}">{sub.get("heading", "")}</h3>'
            sections_html += sub.get("content", "")
        sections_html += '</section>'
    
    # Build FAQ HTML with Schema.org markup
    faq_html = '<section class="faq"><h2>Najczęściej zadawane pytania (FAQ)</h2>'
    faq_html += '<div itemscope itemtype="https://schema.org/FAQPage">'
    for faq in article.get("faq", []):
        faq_html += f'''<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
            <h3 itemprop="name">{faq.get("question", "")}</h3>
            <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
                <p itemprop="text">{faq.get("answer", "")}</p>
            </div>
        </div>'''
    faq_html += '</div></section>'
    
    # Build sources HTML
    sources_html = '<section class="sources"><h2>Źródła</h2><ul>'
    for src in article.get("sources", []):
        sources_html += f'<li><a href="{src.get("url", "#")}" target="_blank" rel="noopener">{src.get("name", "")}</a> ({src.get("type", "")})</li>'
    sources_html += '</ul></section>'
    
    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{meta_desc}">
    <title>{meta_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 24px;
            color: hsl(222, 47%, 20%);
            background: white;
        }}
        h1 {{
            font-family: 'Instrument Serif', Georgia, serif;
            color: hsl(222, 47%, 11%);
            font-size: 2.2em;
            font-weight: 400;
            margin-bottom: 0.6em;
            line-height: 1.2;
        }}
        h2 {{
            font-family: 'Instrument Serif', Georgia, serif;
            color: #04389E;
            font-size: 1.6em;
            font-weight: 400;
            margin-top: 2em;
            margin-bottom: 0.6em;
            padding-bottom: 8px;
            border-bottom: 2px solid hsl(34, 90%, 88%);
        }}
        h3 {{
            font-family: 'Instrument Serif', Georgia, serif;
            color: hsl(220, 95%, 28%);
            font-size: 1.2em;
            font-weight: 400;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        p {{ margin-bottom: 1em; }}
        ul, ol {{ margin-bottom: 1em; padding-left: 24px; }}
        li {{ margin-bottom: 4px; }}
        strong {{ color: hsl(222, 47%, 11%); }}
        a {{ color: #04389E; text-decoration: underline; text-underline-offset: 3px; }}
        .toc {{
            background: hsl(35, 35%, 97%);
            padding: 20px 28px;
            border-radius: 12px;
            margin: 24px 0;
            border: 1px solid hsl(214, 18%, 88%);
        }}
        .toc h2 {{ margin-top: 0; border: none; font-size: 1.2em; padding-bottom: 0; }}
        .toc ol {{ padding-left: 20px; }}
        .toc a {{ color: #04389E; text-decoration: none; }}
        .toc a:hover {{ text-decoration: underline; }}
        .faq {{
            background: hsl(35, 35%, 97%);
            padding: 24px;
            border-radius: 12px;
            margin-top: 2em;
            border: 1px solid hsl(214, 18%, 88%);
        }}
        .faq h3 {{ color: #04389E; }}
        .sources {{
            margin-top: 2em;
            padding-top: 1.5em;
            border-top: 2px solid hsl(34, 90%, 88%);
        }}
        .sources a {{ color: #04389E; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid hsl(214, 18%, 88%);
        }}
        table thead {{ background: hsl(220, 95%, 96%); }}
        table th {{
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            color: #04389E;
            border-bottom: 2px solid hsl(214, 18%, 85%);
        }}
        table td {{
            padding: 10px 14px;
            border-bottom: 1px solid hsl(214, 18%, 93%);
        }}
        table tr:last-child td {{ border-bottom: none; }}
        .callout {{
            border-radius: 10px;
            padding: 16px 18px;
            margin: 16px 0;
            border-left: 4px solid;
            line-height: 1.6;
        }}
        .callout-tip {{ background: hsl(158, 55%, 95%); border-left-color: hsl(158, 55%, 34%); }}
        .callout-warning {{ background: hsl(34, 90%, 95%); border-left-color: #F28C28; }}
        .callout-info {{ background: hsl(220, 95%, 96%); border-left-color: #04389E; }}
        img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0; }}
        @media print {{
            body {{ padding: 0; }}
            .toc {{ break-after: page; }}
        }}
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
        textColor='#04389E'
    )
    
    h3_style = ParagraphStyle(
        'H3Style',
        parent=styles['Heading3'],
        fontName='DejaVuSans-Bold',
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        textColor='#1a3a6e'
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
        textColor='#04389E'
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
