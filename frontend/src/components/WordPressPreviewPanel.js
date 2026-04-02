import React, { useState, useCallback } from 'react';
import { Globe, Loader2, RefreshCw, ExternalLink } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const WordPressPreviewPanel = ({ articleId }) => {
  const [loading, setLoading] = useState(false);
  const [previewHtml, setPreviewHtml] = useState(null);

  const loadPreview = useCallback(async () => {
    if (!articleId) return;
    setLoading(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/export`, {
        format: 'wordpress'
      });
      setPreviewHtml(res.data.content);
    } catch (err) {
      toast.error('Blad ladowania podgladu');
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  const openInNewTab = () => {
    if (!previewHtml) return;
    const fullHtml = `<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Podglad WordPress</title><style>body{margin:0;padding:24px;background:#f5f5f5;}</style></head><body>${previewHtml}</body></html>`;
    const blob = new Blob([fullHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  if (!previewHtml && !loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }} data-testid="wp-preview-panel">
        <Globe size={32} style={{ color: 'hsl(215, 16%, 70%)', margin: '0 auto 12px', display: 'block' }} />
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 6 }}>Podglad WordPress</h3>
        <p style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)', marginBottom: 16, lineHeight: 1.5 }}>
          Zobacz jak artykul bedzie wygladal po opublikowaniu na WordPress — z identycznym formatowaniem, czcionkami i kolorami.
        </p>
        <Button onClick={loadPreview} className="gap-2" size="sm" data-testid="wp-preview-load-btn">
          <Globe size={14} />
          Zaladuj podglad
        </Button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }} data-testid="wp-preview-panel">
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '8px 12px', borderBottom: '1px solid hsl(214, 18%, 90%)',
        background: 'hsl(35, 35%, 98%)'
      }}>
        <Globe size={14} style={{ color: '#04389E' }} />
        <span style={{ fontSize: 12, fontWeight: 600, color: '#04389E', flex: 1 }}>WordPress Preview</span>
        <Button variant="ghost" size="sm" onClick={loadPreview} disabled={loading}
          style={{ padding: '4px 8px', height: 'auto' }} data-testid="wp-preview-refresh-btn">
          {loading ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
        </Button>
        {previewHtml && (
          <Button variant="ghost" size="sm" onClick={openInNewTab}
            style={{ padding: '4px 8px', height: 'auto' }} data-testid="wp-preview-newtab-btn">
            <ExternalLink size={12} />
          </Button>
        )}
      </div>

      {loading ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
        </div>
      ) : (
        <div style={{ flex: 1, overflow: 'auto', background: '#f5f5f5', padding: 12 }}>
          <div
            style={{
              background: 'white',
              borderRadius: 8,
              boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
              overflow: 'hidden'
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
