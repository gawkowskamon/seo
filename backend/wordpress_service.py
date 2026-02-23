"""
WordPress Integration Service
- Publish articles to WordPress via WP REST API
- Generate downloadable WordPress plugin
- Styled HTML output matching in-app editor
"""

import httpx
import base64
import logging
import re

logger = logging.getLogger(__name__)

# ============ Inline Style Definitions (matching App.css visual-editor-canvas) ============

FONTS_IMPORT = '@import url("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap");'

STYLE_WRAPPER = (
    'font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, sans-serif; '
    'line-height: 1.8; max-width: 800px; margin: 0 auto; padding: 40px 24px; '
    'color: hsl(222, 47%, 20%); background: #fff;'
)

STYLE_H2 = (
    'font-family: "Instrument Serif", Georgia, serif; font-size: 26px; font-weight: 400; '
    'color: #04389E; margin: 32px 0 16px; padding-bottom: 8px; '
    'border-bottom: 2px solid hsl(34, 90%, 88%);'
)

STYLE_H3 = (
    'font-family: "Instrument Serif", Georgia, serif; font-size: 19px; font-weight: 400; '
    'color: hsl(220, 95%, 28%); margin: 24px 0 12px;'
)

STYLE_P = 'margin-bottom: 16px; color: hsl(222, 47%, 20%);'

STYLE_UL = 'margin-bottom: 16px; padding-left: 24px;'
STYLE_OL = 'margin-bottom: 16px; padding-left: 24px;'
STYLE_LI = 'margin-bottom: 4px;'

STYLE_STRONG = 'color: hsl(222, 47%, 11%);'

STYLE_A = 'color: #04389E; text-decoration: underline; text-underline-offset: 3px;'

STYLE_BLOCKQUOTE = (
    'border-left: 4px solid #04389E; padding: 12px 16px; margin: 16px 0; '
    'background: hsl(220, 95%, 98%); border-radius: 0 8px 8px 0; '
    'color: hsl(222, 47%, 25%); font-style: italic;'
)

STYLE_HR = 'border: none; border-top: 2px solid hsl(34, 90%, 88%); margin: 24px 0;'

STYLE_IMG = 'max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0;'

STYLE_TABLE = (
    'width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; '
    'border-radius: 8px; overflow: hidden; border: 1px solid hsl(214, 18%, 88%);'
)

STYLE_TH = (
    'padding: 10px 14px; text-align: left; font-weight: 600; font-size: 13px; '
    'color: #04389E; border-bottom: 2px solid hsl(214, 18%, 85%); '
    'background: hsl(220, 95%, 96%); font-family: "IBM Plex Sans", sans-serif;'
)

STYLE_TD = 'padding: 10px 14px; border-bottom: 1px solid hsl(214, 18%, 93%); color: hsl(222, 47%, 20%);'

STYLE_TOC = (
    'background: hsl(35, 35%, 97%); padding: 20px 28px; border-radius: 12px; '
    'margin: 24px 0; border: 1px solid hsl(214, 18%, 88%);'
)

STYLE_TOC_H2 = (
    'font-family: "Instrument Serif", Georgia, serif; font-size: 1.2em; font-weight: 400; '
    'color: #04389E; margin: 0 0 12px; padding-bottom: 0; border: none;'
)

STYLE_FAQ_WRAPPER = (
    'background: hsl(35, 35%, 97%); padding: 24px; border-radius: 12px; '
    'margin-top: 2em; border: 1px solid hsl(214, 18%, 88%);'
)

STYLE_FAQ_H3 = (
    'font-family: "Instrument Serif", Georgia, serif; font-size: 19px; font-weight: 400; '
    'color: #04389E; margin: 24px 0 12px;'
)

STYLE_SOURCES = (
    'margin-top: 2em; padding-top: 1.5em; border-top: 2px solid hsl(34, 90%, 88%);'
)

STYLE_CALLOUT_BASE = (
    'border-radius: 10px; padding: 16px 18px; margin: 16px 0; '
    'font-size: 14px; line-height: 1.6; border-left: 4px solid;'
)
STYLE_CALLOUT_TIP = STYLE_CALLOUT_BASE + ' background: hsl(158, 55%, 95%); border-left-color: hsl(158, 55%, 34%); color: hsl(158, 30%, 20%);'
STYLE_CALLOUT_WARNING = STYLE_CALLOUT_BASE + ' background: hsl(34, 90%, 95%); border-left-color: #F28C28; color: hsl(34, 50%, 20%);'
STYLE_CALLOUT_INFO = STYLE_CALLOUT_BASE + ' background: hsl(220, 95%, 96%); border-left-color: #04389E; color: hsl(220, 50%, 20%);'


def _apply_inline_styles(html_fragment: str) -> str:
    """Apply inline styles to HTML elements within a content fragment."""
    # h2 (skip ones already inside styled containers)
    html_fragment = re.sub(
        r'<h2([^>]*)>',
        lambda m: f'<h2{m.group(1)} style="{STYLE_H2}">',
        html_fragment
    )
    # h3
    html_fragment = re.sub(
        r'<h3([^>]*)>',
        lambda m: f'<h3{m.group(1)} style="{STYLE_H3}">',
        html_fragment
    )
    # p
    html_fragment = re.sub(
        r'<p([^>]*)>',
        lambda m: f'<p{m.group(1)} style="{STYLE_P}">',
        html_fragment
    )
    # ul
    html_fragment = re.sub(
        r'<ul([^>]*)>',
        lambda m: f'<ul{m.group(1)} style="{STYLE_UL}">',
        html_fragment
    )
    # ol
    html_fragment = re.sub(
        r'<ol([^>]*)>',
        lambda m: f'<ol{m.group(1)} style="{STYLE_OL}">',
        html_fragment
    )
    # li
    html_fragment = re.sub(
        r'<li([^>]*)>',
        lambda m: f'<li{m.group(1)} style="{STYLE_LI}">',
        html_fragment
    )
    # strong
    html_fragment = re.sub(
        r'<strong([^>]*)>',
        lambda m: f'<strong{m.group(1)} style="{STYLE_STRONG}">',
        html_fragment
    )
    # a
    html_fragment = re.sub(
        r'<a([^>]*)>',
        lambda m: f'<a{m.group(1)} style="{STYLE_A}">',
        html_fragment
    )
    # blockquote
    html_fragment = re.sub(
        r'<blockquote([^>]*)>',
        lambda m: f'<blockquote{m.group(1)} style="{STYLE_BLOCKQUOTE}">',
        html_fragment
    )
    # hr
    html_fragment = re.sub(
        r'<hr([^>]*)(/?)>',
        lambda m: f'<hr{m.group(1)} style="{STYLE_HR}"{m.group(2)}>',
        html_fragment
    )
    # img
    html_fragment = re.sub(
        r'<img([^>]*)>',
        lambda m: f'<img{m.group(1)} style="{STYLE_IMG}">',
        html_fragment
    )
    # table
    html_fragment = re.sub(
        r'<table([^>]*)>',
        lambda m: f'<table{m.group(1)} style="{STYLE_TABLE}">',
        html_fragment
    )
    # th
    html_fragment = re.sub(
        r'<th([^>]*)>',
        lambda m: f'<th{m.group(1)} style="{STYLE_TH}">',
        html_fragment
    )
    # td
    html_fragment = re.sub(
        r'<td([^>]*)>',
        lambda m: f'<td{m.group(1)} style="{STYLE_TD}">',
        html_fragment
    )
    # callout divs
    html_fragment = re.sub(
        r'<div([^>]*class="[^"]*callout-tip[^"]*"[^>]*)>',
        lambda m: f'<div{m.group(1)} style="{STYLE_CALLOUT_TIP}">',
        html_fragment
    )
    html_fragment = re.sub(
        r'<div([^>]*class="[^"]*callout-warning[^"]*"[^>]*)>',
        lambda m: f'<div{m.group(1)} style="{STYLE_CALLOUT_WARNING}">',
        html_fragment
    )
    html_fragment = re.sub(
        r'<div([^>]*class="[^"]*callout-info[^"]*"[^>]*)>',
        lambda m: f'<div{m.group(1)} style="{STYLE_CALLOUT_INFO}">',
        html_fragment
    )
    return html_fragment


def strip_html_tags(html: str) -> str:
    """Strip HTML tags for excerpt."""
    return re.sub(r'<[^>]+>', '', html).strip()


def _build_styled_content(article: dict) -> str:
    """Build fully styled HTML content for WordPress, matching the in-app editor."""
    parts = []

    # Table of contents
    toc = article.get("toc", [])
    if toc:
        toc_items = ""
        for item in toc:
            toc_items += f'<li style="{STYLE_LI}"><a href="#{item.get("anchor", "")}" style="{STYLE_A}">{item.get("label", item.get("title", ""))}</a></li>'
        parts.append(
            f'<div style="{STYLE_TOC}">'
            f'<h2 style="{STYLE_TOC_H2}">Spis treści</h2>'
            f'<ol style="{STYLE_OL}">{toc_items}</ol>'
            f'</div>'
        )

    # Sections with inline styles applied to content fragments
    for section in article.get("sections", []):
        anchor = section.get("anchor", "")
        heading = section.get("heading", "")
        content = _apply_inline_styles(section.get("content", ""))
        parts.append(f'<h2 id="{anchor}" style="{STYLE_H2}">{heading}</h2>')
        parts.append(content)
        for sub in section.get("subsections", []):
            sub_anchor = sub.get("anchor", "")
            sub_heading = sub.get("heading", "")
            sub_content = _apply_inline_styles(sub.get("content", ""))
            parts.append(f'<h3 id="{sub_anchor}" style="{STYLE_H3}">{sub_heading}</h3>')
            parts.append(sub_content)

    # FAQ with Schema.org + styling
    faq = article.get("faq", [])
    if faq:
        faq_items = ""
        for q in faq:
            faq_items += (
                f'<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">'
                f'<h3 itemprop="name" style="{STYLE_FAQ_H3}">{q.get("question", "")}</h3>'
                f'<div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">'
                f'<p itemprop="text" style="{STYLE_P}">{q.get("answer", "")}</p>'
                f'</div></div>'
            )
        parts.append(
            f'<div style="{STYLE_FAQ_WRAPPER}" itemscope itemtype="https://schema.org/FAQPage">'
            f'<h2 style="{STYLE_TOC_H2}">Najczęściej zadawane pytania (FAQ)</h2>'
            f'{faq_items}</div>'
        )

    # Sources
    sources = article.get("sources", [])
    if sources:
        source_items = ""
        for src in sources:
            source_items += (
                f'<li style="{STYLE_LI}">'
                f'<a href="{src.get("url", "#")}" target="_blank" rel="noopener" style="{STYLE_A}">'
                f'{src.get("name", "")}</a> ({src.get("type", "")})</li>'
            )
        parts.append(
            f'<div style="{STYLE_SOURCES}">'
            f'<h2 style="{STYLE_H2}">Źródła</h2>'
            f'<ul style="{STYLE_UL}">{source_items}</ul></div>'
        )

    inner_html = "\n".join(parts)

    # Wrap everything in a styled container div
    styled_html = (
        f'<style>{FONTS_IMPORT}</style>'
        f'<div style="{STYLE_WRAPPER}">'
        f'{inner_html}'
        f'</div>'
    )
    return styled_html


def build_styled_wordpress_content(article: dict) -> str:
    """Public wrapper: returns styled HTML content for WordPress export."""
    return _build_styled_content(article)


async def publish_to_wordpress(wp_url: str, wp_user: str, wp_app_password: str, article: dict) -> dict:
    """
    Publish an article to WordPress via REST API.
    """
    # Normalize URL - add protocol if missing
    clean_url = wp_url.strip().rstrip('/')
    if not clean_url.startswith('http://') and not clean_url.startswith('https://'):
        clean_url = f"https://{clean_url}"
    
    # Build styled HTML content matching in-app editor
    content_html = _build_styled_content(article)
    
    # Build excerpt
    excerpt = article.get("meta_description", "")
    if not excerpt:
        sections = article.get("sections", [])
        if sections:
            excerpt = strip_html_tags(sections[0].get("content", ""))[:300]
    
    # Prepare WP REST API payload
    wp_api_url = f"{clean_url}/wp-json/wp/v2/posts"
    
    post_data = {
        "title": article.get("title", "Bez tytułu"),
        "content": content_html,
        "excerpt": excerpt,
        "status": "draft",
        "slug": article.get("slug", ""),
        "meta": {
            "_yoast_wpseo_metadesc": article.get("meta_description", ""),
            "_yoast_wpseo_title": article.get("meta_title", ""),
            "_yoast_wpseo_focuskw": article.get("primary_keyword", ""),
        }
    }
    
    # Auth header (Basic Auth with Application Password)
    credentials = base64.b64encode(f"{wp_user}:{wp_app_password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "User-Agent": "KurdynowskiSEO/1.0"
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.post(wp_api_url, json=post_data, headers=headers)
        except httpx.ConnectError:
            return {"success": False, "error": f"Nie mozna polaczyc z {clean_url}. Sprawdz adres WordPress w ustawieniach."}
        except httpx.TimeoutException:
            return {"success": False, "error": f"Timeout polaczenia z WordPress ({clean_url})."}
        
        if response.status_code == 404:
            # Try with index.php in path
            alt_url = f"{clean_url}/index.php/wp-json/wp/v2/posts"
            try:
                response = await client.post(alt_url, json=post_data, headers=headers)
            except Exception:
                pass
            if response.status_code == 404:
                return {"success": False, "error": f"WordPress REST API niedostepne ({clean_url}). Sprawdz czy adres jest poprawny i REST API jest wlaczone."}
        
        if response.status_code in (200, 201):
            data = response.json()
            return {
                "success": True,
                "post_id": data.get("id"),
                "post_url": data.get("link", ""),
                "edit_url": f"{clean_url}/wp-admin/post.php?post={data.get('id')}&action=edit",
                "status": data.get("status", "draft")
            }
        else:
            error_msg = "Nieznany blad"
            try:
                err_data = response.json()
                error_msg = err_data.get("message", str(response.status_code))
            except Exception:
                error_msg = f"HTTP {response.status_code}"
            
            if response.status_code == 401:
                error_msg = "Bledne dane logowania WordPress. Sprawdz uzytkownika i haslo aplikacji w ustawieniach."
            elif response.status_code == 403:
                error_msg = "Brak uprawnien do publikacji na WordPress. Uzytkownik musi miec uprawnienia autora/redaktora."
            
            logger.error(f"WordPress publish failed: {response.status_code} - {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }


def generate_wordpress_plugin(api_base_url: str) -> str:
    """
    Generate a WordPress plugin PHP file that integrates with the Kurdynowski API.
    
    Args:
        api_base_url: The base URL of the Kurdynowski API (e.g. https://seo-article-builder-2.preview.emergentagent.com/api)
    
    Returns:
        PHP code as string
    """
    plugin_code = """<?php
/**
 * Plugin Name: Kurdynowski SEO Article Importer
 * Plugin URI: https://kurdynowski.pl
 * Description: Importuje artykuly SEO z platformy Kurdynowski Article Builder bezposrednio do WordPress.
 * Version: 1.0.0
 * Author: Kurdynowski Accounting & Tax Solutions
 * Author URI: https://kurdynowski.pl
 * License: GPL v2 or later
 * Text Domain: kurdynowski-importer
 */

if (!defined('ABSPATH')) {
    exit;
}

// ============ SETTINGS PAGE ============

add_action('admin_menu', 'kurdynowski_admin_menu');

function kurdynowski_admin_menu() {
    add_menu_page(
        'Kurdynowski Importer',
        'Kurdynowski',
        'manage_options',
        'kurdynowski-importer',
        'kurdynowski_settings_page',
        'dashicons-media-text',
        30
    );
    add_submenu_page(
        'kurdynowski-importer',
        'Ustawienia',
        'Ustawienia',
        'manage_options',
        'kurdynowski-importer',
        'kurdynowski_settings_page'
    );
    add_submenu_page(
        'kurdynowski-importer',
        'Importuj artykuly',
        'Importuj artykuly',
        'manage_options',
        'kurdynowski-import',
        'kurdynowski_import_page'
    );
}

add_action('admin_init', 'kurdynowski_register_settings');

function kurdynowski_register_settings() {
    register_setting('kurdynowski_settings', 'kurdynowski_api_url');
    register_setting('kurdynowski_settings', 'kurdynowski_api_email');
    register_setting('kurdynowski_settings', 'kurdynowski_api_password');
}

function kurdynowski_settings_page() {
    ?>
    <div class="wrap">
        <h1><span class="dashicons dashicons-media-text" style="font-size:28px;margin-right:8px;"></span> Kurdynowski Importer - Ustawienia</h1>
        <form method="post" action="options.php">
            <?php settings_fields('kurdynowski_settings'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row">Adres API</th>
                    <td>
                        <input type="url" name="kurdynowski_api_url" value="<?php echo esc_attr(get_option('kurdynowski_api_url', '""" + api_base_url + """')); ?>" class="regular-text" />
                        <p class="description">Adres API platformy Kurdynowski (np. https://twoja-strona.com/api)</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Email</th>
                    <td>
                        <input type="email" name="kurdynowski_api_email" value="<?php echo esc_attr(get_option('kurdynowski_api_email', '')); ?>" class="regular-text" />
                    </td>
                </tr>
                <tr>
                    <th scope="row">Haslo</th>
                    <td>
                        <input type="password" name="kurdynowski_api_password" value="<?php echo esc_attr(get_option('kurdynowski_api_password', '')); ?>" class="regular-text" />
                    </td>
                </tr>
            </table>
            <?php submit_button('Zapisz ustawienia'); ?>
        </form>
        
        <hr />
        <h2>Test polaczenia</h2>
        <button id="kurdynowski-test-btn" class="button button-secondary">Testuj polaczenie</button>
        <div id="kurdynowski-test-result" style="margin-top:10px;"></div>
        
        <script>
        document.getElementById('kurdynowski-test-btn').addEventListener('click', function() {
            var result = document.getElementById('kurdynowski-test-result');
            result.innerHTML = '<span style="color:#666;">Testowanie...</span>';
            
            fetch(ajaxurl, {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'action=kurdynowski_test_connection'
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    result.innerHTML = '<span style="color:green;">&#10004; Polaczenie OK! Zalogowano jako: ' + data.data.user + '</span>';
                } else {
                    result.innerHTML = '<span style="color:red;">&#10008; Blad: ' + (data.data || 'Nieznany blad') + '</span>';
                }
            })
            .catch(e => {
                result.innerHTML = '<span style="color:red;">&#10008; Blad sieci: ' + e.message + '</span>';
            });
        });
        </script>
    </div>
    <?php
}


// ============ IMPORT PAGE ============

function kurdynowski_import_page() {
    ?>
    <div class="wrap">
        <h1><span class="dashicons dashicons-download" style="font-size:28px;margin-right:8px;"></span> Importuj artykuly</h1>
        
        <div id="kurdynowski-articles-list">
            <p>Ladowanie artykulow...</p>
        </div>
        
        <style>
            .kurdynowski-article-row {
                background: #fff;
                border: 1px solid #ccd0d4;
                padding: 15px 20px;
                margin-bottom: 8px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .kurdynowski-article-row:hover { border-color: #0073aa; }
            .kurdynowski-article-title { font-weight: 600; font-size: 14px; }
            .kurdynowski-article-meta { color: #666; font-size: 12px; margin-top: 4px; }
            .kurdynowski-seo-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
            }
            .kurdynowski-seo-good { background: #d4edda; color: #155724; }
            .kurdynowski-seo-ok { background: #fff3cd; color: #856404; }
            .kurdynowski-seo-bad { background: #f8d7da; color: #721c24; }
        </style>
        
        <script>
        (function() {
            var apiUrl = '<?php echo esc_js(get_option("kurdynowski_api_url", "")); ?>';
            
            function loadArticles() {
                fetch(ajaxurl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'action=kurdynowski_list_articles'
                })
                .then(r => r.json())
                .then(data => {
                    var container = document.getElementById('kurdynowski-articles-list');
                    if (!data.success || !data.data.articles) {
                        container.innerHTML = '<div class="notice notice-error"><p>Blad ladowania: ' + (data.data || 'Sprawdz ustawienia') + '</p></div>';
                        return;
                    }
                    
                    var articles = data.data.articles;
                    if (articles.length === 0) {
                        container.innerHTML = '<div class="notice notice-info"><p>Brak artykulow do importu.</p></div>';
                        return;
                    }
                    
                    var html = '';
                    articles.forEach(function(a) {
                        var seoClass = a.seo_score >= 80 ? 'kurdynowski-seo-good' : (a.seo_score >= 60 ? 'kurdynowski-seo-ok' : 'kurdynowski-seo-bad');
                        html += '<div class="kurdynowski-article-row" data-id="' + a.id + '">';
                        html += '<div>';
                        html += '<div class="kurdynowski-article-title">' + (a.title || 'Bez tytulu') + '</div>';
                        html += '<div class="kurdynowski-article-meta">';
                        html += '<span class="kurdynowski-seo-badge ' + seoClass + '">SEO: ' + (a.seo_score || 0) + '%</span> ';
                        html += (a.primary_keyword || '') + ' &middot; ' + (a.created_at ? new Date(a.created_at).toLocaleDateString('pl-PL') : '');
                        html += '</div></div>';
                        html += '<button class="button button-primary kurdynowski-import-btn" data-id="' + a.id + '">Importuj jako szkic</button>';
                        html += '</div>';
                    });
                    container.innerHTML = html;
                    
                    // Attach import handlers
                    document.querySelectorAll('.kurdynowski-import-btn').forEach(function(btn) {
                        btn.addEventListener('click', function() {
                            importArticle(this.dataset.id, this);
                        });
                    });
                })
                .catch(function(e) {
                    document.getElementById('kurdynowski-articles-list').innerHTML = '<div class="notice notice-error"><p>Blad sieci: ' + e.message + '</p></div>';
                });
            }
            
            function importArticle(articleId, btn) {
                btn.disabled = true;
                btn.textContent = 'Importowanie...';
                
                fetch(ajaxurl, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: 'action=kurdynowski_import_article&article_id=' + encodeURIComponent(articleId)
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        btn.textContent = 'Zaimportowano!';
                        btn.classList.remove('button-primary');
                        btn.classList.add('button-secondary');
                        btn.style.color = 'green';
                        if (data.data.edit_url) {
                            btn.insertAdjacentHTML('afterend', ' <a href="' + data.data.edit_url + '" class="button button-small">Edytuj w WP</a>');
                        }
                    } else {
                        btn.textContent = 'Blad!';
                        btn.style.color = 'red';
                        alert('Blad importu: ' + (data.data || 'Nieznany blad'));
                        setTimeout(function() {
                            btn.textContent = 'Importuj jako szkic';
                            btn.disabled = false;
                            btn.style.color = '';
                        }, 3000);
                    }
                })
                .catch(function(e) {
                    btn.textContent = 'Blad!';
                    alert('Blad sieci: ' + e.message);
                });
            }
            
            loadArticles();
        })();
        </script>
    </div>
    <?php
}


// ============ AJAX HANDLERS ============

add_action('wp_ajax_kurdynowski_test_connection', 'kurdynowski_ajax_test_connection');

function kurdynowski_ajax_test_connection() {
    $token = kurdynowski_get_token();
    if (is_wp_error($token)) {
        wp_send_json_error($token->get_error_message());
    }
    
    $api_url = rtrim(get_option('kurdynowski_api_url', ''), '/');
    $response = wp_remote_get($api_url . '/users/me', array(
        'headers' => array('Authorization' => 'Bearer ' . $token),
        'timeout' => 15
    ));
    
    if (is_wp_error($response)) {
        wp_send_json_error($response->get_error_message());
    }
    
    $body = json_decode(wp_remote_retrieve_body($response), true);
    wp_send_json_success(array('user' => $body['email'] ?? 'OK'));
}


add_action('wp_ajax_kurdynowski_list_articles', 'kurdynowski_ajax_list_articles');

function kurdynowski_ajax_list_articles() {
    $token = kurdynowski_get_token();
    if (is_wp_error($token)) {
        wp_send_json_error($token->get_error_message());
    }
    
    $api_url = rtrim(get_option('kurdynowski_api_url', ''), '/');
    $response = wp_remote_get($api_url . '/articles', array(
        'headers' => array('Authorization' => 'Bearer ' . $token),
        'timeout' => 15
    ));
    
    if (is_wp_error($response)) {
        wp_send_json_error($response->get_error_message());
    }
    
    $body = json_decode(wp_remote_retrieve_body($response), true);
    wp_send_json_success(array('articles' => $body));
}


add_action('wp_ajax_kurdynowski_import_article', 'kurdynowski_ajax_import_article');

function kurdynowski_ajax_import_article() {
    $article_id = sanitize_text_field($_POST['article_id'] ?? '');
    if (empty($article_id)) {
        wp_send_json_error('Brak ID artykulu');
    }
    
    $token = kurdynowski_get_token();
    if (is_wp_error($token)) {
        wp_send_json_error($token->get_error_message());
    }
    
    $api_url = rtrim(get_option('kurdynowski_api_url', ''), '/');
    
    // Get full article with styled export (inline styles for WordPress)
    $response = wp_remote_post($api_url . '/articles/' . $article_id . '/export', array(
        'headers' => array(
            'Authorization' => 'Bearer ' . $token,
            'Content-Type' => 'application/json'
        ),
        'body' => json_encode(array('format' => 'wordpress')),
        'timeout' => 30
    ));
    
    if (is_wp_error($response)) {
        wp_send_json_error($response->get_error_message());
    }
    
    $export = json_decode(wp_remote_retrieve_body($response), true);
    $html_content = $export['content'] ?? '';
    
    // Get article metadata
    $meta_response = wp_remote_get($api_url . '/articles/' . $article_id, array(
        'headers' => array('Authorization' => 'Bearer ' . $token),
        'timeout' => 15
    ));
    
    $article = json_decode(wp_remote_retrieve_body($meta_response), true);
    
    // Content from wordpress format is already ready for WP (inline styles, no html/body wrapper)
    
    // Create WP post
    $post_data = array(
        'post_title'   => $article['title'] ?? 'Artykul z Kurdynowski',
        'post_content' => $html_content,
        'post_excerpt'  => $article['meta_description'] ?? '',
        'post_status'  => 'draft',
        'post_type'    => 'post',
    );
    
    $post_id = wp_insert_post($post_data);
    
    if (is_wp_error($post_id)) {
        wp_send_json_error($post_id->get_error_message());
    }
    
    // Set Yoast SEO meta if plugin is active
    if (function_exists('update_post_meta')) {
        update_post_meta($post_id, '_yoast_wpseo_metadesc', $article['meta_description'] ?? '');
        update_post_meta($post_id, '_yoast_wpseo_title', $article['meta_title'] ?? '');
        update_post_meta($post_id, '_yoast_wpseo_focuskw', $article['primary_keyword'] ?? '');
    }
    
    wp_send_json_success(array(
        'post_id' => $post_id,
        'edit_url' => admin_url('post.php?post=' . $post_id . '&action=edit')
    ));
}


// ============ HELPERS ============

function kurdynowski_get_token() {
    $api_url = rtrim(get_option('kurdynowski_api_url', ''), '/');
    $email = get_option('kurdynowski_api_email', '');
    $password = get_option('kurdynowski_api_password', '');
    
    if (empty($api_url) || empty($email) || empty($password)) {
        return new WP_Error('config', 'Uzupelnij ustawienia API w Kurdynowski > Ustawienia');
    }
    
    $response = wp_remote_post($api_url . '/auth/login', array(
        'headers' => array('Content-Type' => 'application/json'),
        'body' => json_encode(array('email' => $email, 'password' => $password)),
        'timeout' => 15
    ));
    
    if (is_wp_error($response)) {
        return new WP_Error('api', 'Blad polaczenia: ' . $response->get_error_message());
    }
    
    $body = json_decode(wp_remote_retrieve_body($response), true);
    
    if (!isset($body['token'])) {
        return new WP_Error('auth', 'Blad logowania - sprawdz dane');
    }
    
    return $body['token'];
}
"""
    return plugin_code
