import React, { useState, useCallback } from 'react';
import { Globe, Loader2, RefreshCw, ExternalLink, Search, FileText, Tag, CheckCircle2, AlertTriangle, Download } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SEOField = ({ label, value, maxLen, icon: Icon }) => {
  const len = (value || '').length;
  const isOk = maxLen ? len > 0 && len <= maxLen : len > 0;
  const isWarn = maxLen && len > maxLen;
  return (
    <div style={{ marginBottom: 10 }} data-testid={`seo-field-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 3 }}>
        <Icon size={11} style={{ color: '#04389E', flexShrink: 0 }} />
        <span style={{ fontSize: 10, fontWeight: 700, color: 'hsl(215, 16%, 40%)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</span>
        {maxLen && (
          <span style={{
            marginLeft: 'auto', fontSize: 10, fontWeight: 600,
            color: isWarn ? 'hsl(0, 70%, 50%)' : isOk ? 'hsl(142, 60%, 35%)' : 'hsl(215, 16%, 55%)'
          }}>
            {len}/{maxLen}
          </span>
        )}
      </div>
      <div style={{
        padding: '6px 9px', borderRadius: 6, fontSize: 12, lineHeight: 1.4,
        background: value ? 'hsl(220, 95%, 98%)' : 'hsl(0, 50%, 97%)',
        border: `1px solid ${value ? 'hsl(214, 18%, 88%)' : 'hsl(0, 50%, 85%)'}`,
        color: value ? 'hsl(222, 47%, 20%)' : 'hsl(0, 50%, 45%)',
        wordBreak: 'break-word'
      }}>
        {value || 'Brak'}
      </div>
    </div>
  );
};

const WordPressPreviewPanel = ({ articleId, article }) => {
  const [loading, setLoading] = useState(false);
  const [previewHtml, setPreviewHtml] = useState(null);
  const [showSeo, setShowSeo] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const metaTitle = article?.meta_title || '';
  const metaDesc = article?.meta_description || '';
  const keyword = article?.primary_keyword || '';
  const slug = article?.slug || '';
  const title = article?.title || '';
  const seoScore = article?.seo_score?.percentage || article?.surfer_score?.percentage || 0;
  const sectionsCount = (article?.sections || []).length;
  const faqCount = (article?.faq || []).length;
  const sourcesCount = (article?.sources || []).length;

  const checks = [
    { ok: metaTitle.length > 0 && metaTitle.length <= 60, label: 'Meta tytul (max 60 znakow)' },
    { ok: metaDesc.length >= 120 && metaDesc.length <= 160, label: 'Meta opis (120-160 znakow)' },
    { ok: keyword.length > 0, label: 'Slowo kluczowe ustawione' },
    { ok: sectionsCount >= 3, label: 'Min. 3 sekcje tresci' },
    { ok: faqCount >= 3, label: 'Min. 3 pytania FAQ' },
    { ok: sourcesCount >= 1, label: 'Zrodla podlinkowane' },
  ];
  const passedChecks = checks.filter(c => c.ok).length;

  const loadPreview = useCallback(async () => {
    if (!articleId) return;
    setLoading(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/export`, { format: 'wordpress' });
      setPreviewHtml(res.data.content);
    } catch (err) {
      toast.error('Blad ladowania podgladu');
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  const openInNewTab = () => {
    if (!previewHtml) return;
    const fullHtml = `<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>body{margin:0;padding:24px;background:#f5f5f5;}</style></head><body>${previewHtml}</body></html>`;
    const blob = new Blob([fullHtml], { type: 'text/html' });
    window.open(URL.createObjectURL(blob), '_blank');
  };

  const downloadPdf = async () => {
    if (!articleId) return;
    setDownloadingPdf(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/surfer/seo-report/${articleId}`, {}, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `raport_seo_${(title || 'artykul').slice(0, 30).replace(/[^\w-]/g, '_')}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Raport PDF pobrany');
    } catch {
      toast.error('Blad generowania PDF');
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (!previewHtml && !loading) {
    return (
      <div style={{ padding: 20 }} data-testid="wp-preview-panel">
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <Globe size={28} style={{ color: 'hsl(215, 16%, 70%)', margin: '0 auto 10px', display: 'block' }} />
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>Podglad WordPress</h3>
          <p style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', marginBottom: 14, lineHeight: 1.5 }}>
            Zobacz jak artykul bedzie wygladal na WordPress z identycznym formatowaniem.
          </p>
          <Button onClick={loadPreview} className="gap-2 w-full" size="sm" data-testid="wp-preview-load-btn">
            <Globe size={14} />
            Zaladuj podglad
          </Button>
        </div>

        {/* SEO readiness check even before loading preview */}
        <div style={{
          background: 'hsl(35, 35%, 97%)', borderRadius: 10, padding: 14,
          border: '1px solid hsl(214, 18%, 88%)'
        }} data-testid="wp-seo-readiness">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
            <Search size={13} style={{ color: '#04389E' }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: '#04389E' }}>
              Gotowość SEO ({passedChecks}/{checks.length})
            </span>
          </div>
          {checks.map((c, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 0', fontSize: 11 }}>
              {c.ok
                ? <CheckCircle2 size={12} style={{ color: 'hsl(142, 60%, 40%)', flexShrink: 0 }} />
                : <AlertTriangle size={12} style={{ color: 'hsl(34, 90%, 50%)', flexShrink: 0 }} />
              }
              <span style={{ color: c.ok ? 'hsl(142, 40%, 30%)' : 'hsl(34, 50%, 30%)' }}>{c.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }} data-testid="wp-preview-panel">
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '7px 12px', borderBottom: '1px solid hsl(214, 18%, 90%)',
        background: 'hsl(35, 35%, 98%)', flexShrink: 0
      }}>
        <Globe size={13} style={{ color: '#04389E' }} />
        <span style={{ fontSize: 11, fontWeight: 700, color: '#04389E', flex: 1 }}>WordPress Preview</span>
        <button
          onClick={() => setShowSeo(p => !p)}
          style={{
            padding: '3px 8px', borderRadius: 5, fontSize: 10, fontWeight: 600,
            background: showSeo ? '#04389E' : 'transparent',
            color: showSeo ? 'white' : '#04389E',
            border: '1px solid #04389E', cursor: 'pointer', transition: 'all 0.15s'
          }}
          data-testid="wp-toggle-seo-btn"
        >
          SEO
        </button>
        <Button variant="ghost" size="sm" onClick={downloadPdf} disabled={downloadingPdf}
          style={{ padding: '3px 7px', height: 'auto' }} data-testid="wp-download-pdf-btn"
          title="Pobierz raport SEO (PDF)">
          {downloadingPdf ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
        </Button>
        <Button variant="ghost" size="sm" onClick={loadPreview} disabled={loading}
          style={{ padding: '3px 7px', height: 'auto' }} data-testid="wp-preview-refresh-btn">
          {loading ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
        </Button>
        <Button variant="ghost" size="sm" onClick={openInNewTab}
          style={{ padding: '3px 7px', height: 'auto' }} data-testid="wp-preview-newtab-btn">
          <ExternalLink size={12} />
        </Button>
      </div>

      {/* SEO Meta Panel (collapsible) */}
      {showSeo && (
        <div style={{
          padding: '10px 12px', borderBottom: '1px solid hsl(214, 18%, 90%)',
          background: 'white', flexShrink: 0
        }} data-testid="wp-seo-meta-section">
          {/* Google SERP preview */}
          <div style={{
            marginBottom: 12, padding: 10, borderRadius: 8,
            border: '1px solid hsl(214, 18%, 90%)', background: 'white'
          }} data-testid="wp-serp-preview">
            <div style={{ fontSize: 9, fontWeight: 700, color: 'hsl(215, 16%, 55%)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
              Podglad w Google
            </div>
            <div style={{ fontSize: 15, color: '#1a0dab', fontWeight: 400, lineHeight: 1.3, marginBottom: 2, fontFamily: 'Arial, sans-serif' }}>
              {metaTitle || title || 'Brak meta tytulu'}
            </div>
            <div style={{ fontSize: 11, color: '#006621', marginBottom: 2, fontFamily: 'Arial, sans-serif' }}>
              twoja-strona.pl › {slug || 'artykul'}
            </div>
            <div style={{ fontSize: 12, color: '#545454', lineHeight: 1.4, fontFamily: 'Arial, sans-serif' }}>
              {metaDesc || 'Brak meta opisu. Dodaj opis aby poprawic widocznosc w wynikach wyszukiwania.'}
            </div>
          </div>

          <SEOField label="Meta tytul" value={metaTitle} maxLen={60} icon={FileText} />
          <SEOField label="Meta opis" value={metaDesc} maxLen={160} icon={FileText} />
          <SEOField label="Slowo kluczowe" value={keyword} icon={Tag} />

          {/* Readiness checklist */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
            {checks.map((c, i) => (
              <span key={i} style={{
                display: 'inline-flex', alignItems: 'center', gap: 3,
                padding: '2px 7px', borderRadius: 20, fontSize: 9, fontWeight: 600,
                background: c.ok ? 'hsl(142, 50%, 94%)' : 'hsl(34, 90%, 95%)',
                color: c.ok ? 'hsl(142, 60%, 30%)' : 'hsl(34, 60%, 35%)'
              }}>
                {c.ok ? <CheckCircle2 size={9} /> : <AlertTriangle size={9} />}
                {c.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Preview content */}
      {loading ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
        </div>
      ) : (
        <div style={{ flex: 1, overflow: 'auto', background: '#f5f5f5', padding: 10 }}>
          <div
            style={{
              background: 'white', borderRadius: 8,
              boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflow: 'hidden'
            }}
            dangerouslySetInnerHTML={{ __html: previewHtml }}
            data-testid="wp-preview-content"
          />
        </div>
      )}
    </div>
  );
};

export default WordPressPreviewPanel;
