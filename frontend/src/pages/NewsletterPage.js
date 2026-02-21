import React, { useState, useEffect } from 'react';
import { Mail, Loader2, Copy, Download, Check, Eye, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const styles = [
  { id: 'informacyjny', label: 'Informacyjny', desc: 'Rzeczowy ton z najważniejszymi faktami' },
  { id: 'ekspercki', label: 'Ekspercki', desc: 'Autorytatywny z odwołaniami do przepisów' },
  { id: 'przyjazny', label: 'Przyjazny', desc: 'Ciepły i przystępny dla klientów' },
];

export default function NewsletterPage() {
  const [articles, setArticles] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [title, setTitle] = useState('');
  const [style, setStyle] = useState('informacyjny');
  const [loading, setLoading] = useState(false);
  const [newsletter, setNewsletter] = useState(null);
  const [history, setHistory] = useState([]);
  const [preview, setPreview] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadArticles();
    loadHistory();
  }, []);

  const loadArticles = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${BACKEND_URL}/api/articles`, { headers: { Authorization: `Bearer ${token}` } });
      setArticles(res.data || []);
    } catch (e) {}
  };

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${BACKEND_URL}/api/newsletter/list`, { headers: { Authorization: `Bearer ${token}` } });
      setHistory(res.data || []);
    } catch (e) {}
  };

  const toggleArticle = (id) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setNewsletter(null);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${BACKEND_URL}/api/newsletter/generate`, {
        title: title || undefined,
        article_ids: selectedIds.length > 0 ? selectedIds : undefined,
        style
      }, { headers: { Authorization: `Bearer ${token}` }, timeout: 60000 });
      setNewsletter(res.data);
      loadHistory();
      toast.success('Newsletter wygenerowany');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Błąd generowania newslettera');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (newsletter?.html) {
      navigator.clipboard.writeText(newsletter.html);
      setCopied(true);
      toast.success('HTML skopiowany');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (newsletter?.html) {
      const blob = new Blob([newsletter.html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `newsletter-${newsletter.id || 'export'}.html`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const loadFromHistory = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${BACKEND_URL}/api/newsletter/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      setNewsletter(res.data);
      setPreview(false);
    } catch (e) { toast.error('Nie można załadować newslettera'); }
  };

  return (
    <div data-testid="newsletter-page" style={{ padding: '32px 40px', maxWidth: 1200 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>
          Generator newslettera
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          Automatycznie generuj profesjonalne newslettery z Twoich artykułów
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: newsletter ? '1fr 1fr' : '1fr', gap: 24 }}>
        {/* Left: Config */}
        <div>
          {/* Title */}
          <div style={{
            background: 'var(--bg-card)', borderRadius: 14, padding: 20, marginBottom: 16,
            border: '1px solid var(--border)'
          }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: 8 }}>
              TYTUŁ NEWSLETTERA
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Cotygodniowy newsletter podatkowy..."
              data-testid="newsletter-title-input"
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)',
                fontSize: 14, background: 'var(--bg-input)', color: 'var(--text-primary)', outline: 'none'
              }}
            />
          </div>

          {/* Style */}
          <div style={{
            background: 'var(--bg-card)', borderRadius: 14, padding: 20, marginBottom: 16,
            border: '1px solid var(--border)'
          }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: 12 }}>
              STYL
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              {styles.map(s => (
                <button key={s.id}
                  onClick={() => setStyle(s.id)}
                  data-testid={`newsletter-style-${s.id}`}
                  style={{
                    flex: 1, padding: '10px 12px', borderRadius: 10, border: '2px solid',
                    borderColor: style === s.id ? 'var(--accent)' : 'var(--border)',
                    background: style === s.id ? 'rgba(4,56,158,0.05)' : 'var(--bg-card)',
                    cursor: 'pointer', textAlign: 'left', transition: 'all 0.15s'
                  }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{s.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{s.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Articles selection */}
          <div style={{
            background: 'var(--bg-card)', borderRadius: 14, padding: 20, marginBottom: 16,
            border: '1px solid var(--border)'
          }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: 12 }}>
              ARTYKUŁY ({selectedIds.length} wybranych)
            </label>
            <div style={{ maxHeight: 250, overflowY: 'auto' }}>
              {articles.map(a => (
                <label key={a.id} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px',
                  borderRadius: 8, cursor: 'pointer', transition: 'background 0.1s',
                  background: selectedIds.includes(a.id) ? 'rgba(4,56,158,0.05)' : 'transparent'
                }}>
                  <input type="checkbox" checked={selectedIds.includes(a.id)} onChange={() => toggleArticle(a.id)}
                    data-testid={`newsletter-article-${a.id}`} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.title}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                      SEO: {a.seo_score?.percentage || 0}%
                    </div>
                  </div>
                </label>
              ))}
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 8 }}>
              Nie wybrano artykułów? AI użyje 5 najnowszych.
            </p>
          </div>

          <Button onClick={handleGenerate} disabled={loading} className="w-full gap-2" data-testid="generate-newsletter-btn">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Mail size={16} />}
            Generuj newsletter
          </Button>

          {/* History */}
          {history.length > 0 && (
            <div style={{
              background: 'var(--bg-card)', borderRadius: 14, padding: 20, marginTop: 16,
              border: '1px solid var(--border)'
            }}>
              <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', display: 'block', marginBottom: 12 }}>
                HISTORIA NEWSLETTERÓW
              </label>
              {history.map((h, i) => (
                <div key={i} onClick={() => loadFromHistory(h.id)}
                  style={{
                    padding: '8px 10px', borderRadius: 8, cursor: 'pointer',
                    borderBottom: i < history.length - 1 ? '1px solid var(--border)' : 'none',
                    transition: 'background 0.1s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>{h.title}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                    {new Date(h.created_at).toLocaleString('pl-PL')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Preview */}
        {newsletter && (
          <div>
            <div style={{
              background: 'var(--bg-card)', borderRadius: 14, border: '1px solid var(--border)',
              overflow: 'hidden'
            }}>
              {/* Preview header */}
              <div style={{
                padding: '12px 16px', borderBottom: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between'
              }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {newsletter.title}
                </span>
                <div style={{ display: 'flex', gap: 6 }}>
                  <Button size="sm" variant="outline" onClick={() => setPreview(p => !p)} data-testid="newsletter-toggle-preview">
                    <Eye size={14} /> {preview ? 'HTML' : 'Podgląd'}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleCopy} data-testid="newsletter-copy-btn">
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleDownload} data-testid="newsletter-download-btn">
                    <Download size={14} />
                  </Button>
                </div>
              </div>
              {/* Content */}
              <div style={{ padding: 0, maxHeight: 600, overflowY: 'auto' }}>
                {preview ? (
                  <div dangerouslySetInnerHTML={{ __html: newsletter.html }}
                    style={{ padding: 0, background: '#fff' }} />
                ) : (
                  <pre style={{
                    padding: 16, fontSize: 11, lineHeight: 1.5, whiteSpace: 'pre-wrap',
                    color: 'var(--text-primary)', fontFamily: 'monospace', margin: 0
                  }}>
                    {newsletter.html}
                  </pre>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
