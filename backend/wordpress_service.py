"""
WordPress Integration Service
- Publish articles to WordPress via WP REST API
- Generate downloadable WordPress plugin
"""

import httpx
import base64
import logging
import re

logger = logging.getLogger(__name__)


def strip_html_tags(html: str) -> str:
    """Strip HTML tags for excerpt."""
    return re.sub(r'<[^>]+>', '', html).strip()


async def publish_to_wordpress(wp_url: str, wp_user: str, wp_app_password: str, article: dict) -> dict:
    """
    Publish an article to WordPress via REST API.
    
    Args:
        wp_url: WordPress site URL (e.g. https://example.com)
        wp_user: WordPress username
        wp_app_password: WordPress Application Password
        article: Article dict from DB
    
    Returns:
        dict with post_id, post_url, status
    """
    # Build the HTML content
    content_html = ""
    
    # Table of contents
    toc = article.get("toc", [])
    if toc:
        content_html += '<div class="toc"><h2>Spis treści</h2><ol>'
        for item in toc:
            content_html += f'<li><a href="#{item["anchor"]}">{item["label"]}</a></li>'
        content_html += '</ol></div>'
    
    # Sections
    for section in article.get("sections", []):
        content_html += f'<h2 id="{section.get("anchor", "")}">{section.get("heading", "")}</h2>'
        content_html += section.get("content", "")
        for sub in section.get("subsections", []):
            content_html += f'<h3 id="{sub.get("anchor", "")}">{sub.get("heading", "")}</h3>'
            content_html += sub.get("content", "")
    
    # FAQ with Schema.org
    faq = article.get("faq", [])
    if faq:
        content_html += '<div class="faq" itemscope itemtype="https://schema.org/FAQPage">'
        content_html += '<h2>Najczęściej zadawane pytania (FAQ)</h2>'
        for q in faq:
            content_html += f'''<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
                <h3 itemprop="name">{q.get("question", "")}</h3>
                <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
                    <p itemprop="text">{q.get("answer", "")}</p>
                </div>
            </div>'''
        content_html += '</div>'
    
    # Sources
    sources = article.get("sources", [])
    if sources:
        content_html += '<div class="sources"><h2>Źródła</h2><ul>'
        for src in sources:
            content_html += f'<li><a href="{src.get("url", "#")}" target="_blank" rel="noopener">{src.get("name", "")}</a> ({src.get("type", "")})</li>'
        content_html += '</ul></div>'
    
    # Build excerpt
    excerpt = article.get("meta_description", "")
    if not excerpt:
        sections = article.get("sections", [])
        if sections:
            excerpt = strip_html_tags(sections[0].get("content", ""))[:300]
    
    # Prepare WP REST API payload
    wp_api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    post_data = {
        "title": article.get("title", "Bez tytułu"),
        "content": content_html,
        "excerpt": excerpt,
        "status": "draft",  # Always publish as draft for safety
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
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(wp_api_url, json=post_data, headers=headers)
        
        if response.status_code in (200, 201):
            data = response.json()
            return {
                "success": True,
                "post_id": data.get("id"),
                "post_url": data.get("link", ""),
                "edit_url": f"{wp_url.rstrip('/')}/wp-admin/post.php?post={data.get('id')}&action=edit",
                "status": data.get("status", "draft")
            }
        else:
            error_msg = "Nieznany blad"
            try:
                err_data = response.json()
                error_msg = err_data.get("message", str(response.status_code))
            except Exception:
                error_msg = f"HTTP {response.status_code}"
            
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
        api_base_url: The base URL of the Kurdynowski API (e.g. https://blog-optimizer-kit.preview.emergentagent.com/api)
    
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
    
    // Get full article with export
    $response = wp_remote_post($api_url . '/articles/' . $article_id . '/export', array(
        'headers' => array(
            'Authorization' => 'Bearer ' . $token,
            'Content-Type' => 'application/json'
        ),
        'body' => json_encode(array('format' => 'html')),
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
    
    // Extract body content from full HTML (strip html/head/body tags)
    if (preg_match('/<body[^>]*>(.*)<\\/body>/is', $html_content, $matches)) {
        $html_content = $matches[1];
    }
    // Strip article wrapper
    if (preg_match('/<article[^>]*>(.*)<\\/article>/is', $html_content, $matches)) {
        $html_content = $matches[1];
    }
    // Remove the h1 title (WP handles it)
    $html_content = preg_replace('/<h1[^>]*>.*?<\\/h1>/is', '', $html_content, 1);
    
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
