import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download, Loader2, Globe, Link2, FileText, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function ImportArticles() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('url'); // url or wordpress
  const [url, setUrl] = useState('');
  const [optimize, setOptimize] = useState(true);
  const [loading, setLoading] = useState(false);
  const [imported, setImported] = useState(null);
  
  // WordPress mode
  const [wpUrl, setWpUrl] = useState('');
  const [wpUser, setWpUser] = useState('');
  const [wpPassword, setWpPassword] = useState('');
  const [wpArticles, setWpArticles] = useState(null);
  const [wpLoading, setWpLoading] = useState(false);
  const [importingWp, setImportingWp] = useState(null);

  const handleImportUrl = async () => {
    if (!url) { toast.error('Podaj adres URL'); return; }
    setLoading(true);
    setImported(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/import/url`, { url, optimize }, { timeout: 120000 });
      setImported(res.data);
      toast.success('Artykul zaimportowany' + (optimize ? ' i zoptymalizowany' : ''));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad importu');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchWp = async () => {
    if (!wpUrl) { toast.error('Podaj adres WordPress'); return; }
    setWpLoading(true);
    setWpArticles(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/import/wordpress`, {
        wp_url: wpUrl, wp_user: wpUser, wp_password: wpPassword, limit: 20
      });
      setWpArticles(res.data.articles);
      toast.success(`Znaleziono ${res.data.count} artykulow`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad polaczenia z WordPress');
    } finally {
      setWpLoading(false);
    }
  };

  const handleImportWpArticle = async (article) => {
    setImportingWp(article.wp_id);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/import/url`, {
        url: article.source_url, optimize: true
      }, { timeout: 120000 });
      setImported(res.data);
      toast.success(`Zaimportowano: ${article.title}`);
    } catch (err) {
      toast.error('Blad importu artykulu');
    } finally {
      setImportingWp(null);
    }
  };

  return (
    <div className="page-container" data-testid="import-page">
      <div className="page-header">
        <div>
          <h1>Import artykulow</h1>
          <p style={{ fontSize: 14, color: 'hsl(215, 16%, 45%)', marginTop: 4 }}>
            Importuj artykuly z URL lub WordPress i zoptymalizuj pod SEO
          </p>
        </div>
      </div>

      {/* Mode tabs */}
      <div style={{
        display: 'flex', borderRadius: 10, border: '1px solid hsl(214, 18%, 88%)',
        marginBottom: 24, overflow: 'hidden', maxWidth: 400
      }}>
        <button onClick={() => setMode('url')} data-testid="import-tab-url"
          style={{
            flex: 1, padding: '10px 0', fontSize: 14, fontWeight: 600,
            border: 'none', cursor: 'pointer',
            background: mode === 'url' ? '#04389E' : 'transparent',
            color: mode === 'url' ? 'white' : 'hsl(215, 16%, 45%)',
            transition: 'all 0.15s'
          }}>
          <Globe size={14} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
          Z adresu URL
        </button>
        <button onClick={() => setMode('wordpress')} data-testid="import-tab-wordpress"
          style={{
            flex: 1, padding: '10px 0', fontSize: 14, fontWeight: 600,
            border: 'none', cursor: 'pointer',
            background: mode === 'wordpress' ? '#04389E' : 'transparent',
            color: mode === 'wordpress' ? 'white' : 'hsl(215, 16%, 45%)',
            transition: 'all 0.15s'
          }}>
          <Link2 size={14} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
          Z WordPress
        </button>
      </div>

      {/* URL Import */}
      {mode === 'url' && (
        <div style={{
          background: 'white', borderRadius: 16, padding: 28,
          border: '1px solid hsl(214, 18%, 88%)', maxWidth: 640
        }}>
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
              Adres URL artykulu
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <Input
                value={url} onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/artykul-seo"
                data-testid="import-url-input"
                style={{ flex: 1 }}
              />
              <Button onClick={handleImportUrl} disabled={loading} className="gap-2"
                data-testid="import-url-btn">
                {loading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                Importuj
              </Button>
            </div>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
            <input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)}
              data-testid="import-optimize-checkbox" />
            <Sparkles size={14} style={{ color: '#F28C28' }} />
            <span>Zoptymalizuj pod SEO za pomoca AI</span>
          </label>
        </div>
      )}

      {/* WordPress Import */}
      {mode === 'wordpress' && (
        <div style={{
          background: 'white', borderRadius: 16, padding: 28,
          border: '1px solid hsl(214, 18%, 88%)', maxWidth: 640
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>Adres WordPress</label>
              <Input value={wpUrl} onChange={(e) => setWpUrl(e.target.value)}
                placeholder="https://twoja-strona.pl" data-testid="import-wp-url" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>Uzytkownik (opcjonalnie)</label>
                <Input value={wpUser} onChange={(e) => setWpUser(e.target.value)} placeholder="admin" />
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>Haslo aplikacji (opcjonalnie)</label>
                <Input type="password" value={wpPassword} onChange={(e) => setWpPassword(e.target.value)} placeholder="xxxx xxxx xxxx" />
              </div>
            </div>
            <Button onClick={handleFetchWp} disabled={wpLoading} className="gap-2"
              data-testid="import-wp-fetch-btn">
              {wpLoading ? <Loader2 size={16} className="animate-spin" /> : <Globe size={16} />}
              Pobierz liste artykulow
            </Button>
          </div>

          {wpArticles && (
            <div style={{ marginTop: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
                Znalezione artykuly ({wpArticles.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {wpArticles.map((a) => (
                  <div key={a.wp_id} style={{
                    padding: '12px 16px', borderRadius: 10,
                    border: '1px solid hsl(214, 18%, 88%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                  }}>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                        dangerouslySetInnerHTML={{ __html: a.title }} />
                      <div style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', marginTop: 2 }}>
                        {a.word_count} slow | {a.date ? new Date(a.date).toLocaleDateString('pl-PL') : ''}
                      </div>
                    </div>
                    <Button size="sm" variant="outline" className="gap-1"
                      disabled={importingWp === a.wp_id}
                      onClick={() => handleImportWpArticle(a)}>
                      {importingWp === a.wp_id ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
                      Importuj
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Import result */}
      {imported && (
        <div style={{
          marginTop: 24, background: 'hsl(142, 50%, 96%)', borderRadius: 16, padding: 24,
          border: '1px solid hsl(142, 50%, 80%)', maxWidth: 640
        }} data-testid="import-result">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <CheckCircle2 size={20} style={{ color: 'hsl(142, 71%, 35%)' }} />
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'hsl(142, 71%, 25%)' }}>
              Artykul zaimportowany
            </h3>
          </div>
          <div style={{ fontSize: 14, color: 'hsl(142, 40%, 25%)', marginBottom: 6 }}>
            <strong>{imported.title}</strong>
          </div>
          {imported.primary_keyword && (
            <div style={{ fontSize: 12, color: 'hsl(142, 40%, 35%)', marginBottom: 12 }}>
              Slowo kluczowe: {imported.primary_keyword}
            </div>
          )}
          <Button onClick={() => navigate(`/editor/${imported.id}`)} className="gap-2" size="sm">
            <ArrowRight size={14} />
            Przejdz do edytora
          </Button>
        </div>
      )}
    </div>
  );
}
