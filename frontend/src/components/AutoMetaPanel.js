import React, { useState, useCallback } from 'react';
import { Wand2, Loader2, CheckCircle, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AutoMetaPanel = ({ articleId, currentMetaTitle, currentMetaDesc, onApply }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/auto-meta/status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('Meta tagi wygenerowane');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd generowania');
      } else {
        setTimeout(() => pollStatus(jobId), 2000);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const generate = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/auto-meta`, { article_id: articleId });
      if (res.data.job_id) setTimeout(() => pollStatus(res.data.job_id), 2000);
    } catch {
      setLoading(false);
      toast.error('Błąd uruchamiania');
    }
  };

  const handleApply = (metaTitle, metaDesc) => {
    if (onApply) {
      onApply(metaTitle, metaDesc);
      toast.success('Meta tagi zastosowane');
    }
  };

  const scoreColor = (s) => s >= 85 ? '#16a34a' : s >= 70 ? '#f59e0b' : '#ef4444';

  return (
    <div className="plagiarism-panel" data-testid="auto-meta-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Wand2 size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Auto meta tagi</span>
        </div>
        <Button size="sm" onClick={generate} disabled={loading || !articleId} className="gap-1" data-testid="auto-meta-generate-button">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
          {loading ? 'Generuję...' : 'Generuj'}
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>AI generuje zoptymalizowane meta tagi...</p>
        </div>
      )}

      {result && !loading && (
        <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Recommended set */}
          {result.recommended && (
            <div className="ab-winner-card" data-testid="auto-meta-recommended">
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <CheckCircle size={14} style={{ color: '#16a34a' }} />
                <span style={{ fontWeight: 600, fontSize: 12, color: '#16a34a' }}>REKOMENDOWANY ZESTAW</span>
              </div>
              <div style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Meta title</span>
                <p style={{ fontSize: 12, fontWeight: 500, marginTop: 2 }}>"{result.recommended.meta_title}"</p>
              </div>
              <div style={{ marginBottom: 6 }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Meta description</span>
                <p style={{ fontSize: 12, marginTop: 2 }}>"{result.recommended.meta_description}"</p>
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6 }}>{result.recommended.reason}</p>
              <Button size="sm" className="gap-1 w-full" onClick={() => handleApply(result.recommended.meta_title, result.recommended.meta_description)} data-testid="auto-meta-apply-recommended">
                Zastosuj <ArrowRight size={14} />
              </Button>
            </div>
          )}

          {/* Title variants */}
          {result.meta_titles?.length > 0 && (
            <div>
              <h4 style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>Warianty meta title</h4>
              {result.meta_titles.map((t, i) => (
                <div key={i} className="ab-variant-card" style={{ marginBottom: 6 }} data-testid="auto-meta-title-variant">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span className="ai-suggest-type" style={{ fontSize: 9 }}>{t.style}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: scoreColor(t.score) }}>{t.score}</span>
                  </div>
                  <p style={{ fontSize: 12, marginBottom: 2 }}>"{t.text}"</p>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{t.length} znaków</span>
                </div>
              ))}
            </div>
          )}

          {/* Description variants */}
          {result.meta_descriptions?.length > 0 && (
            <div>
              <h4 style={{ fontSize: 12, fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>Warianty meta description</h4>
              {result.meta_descriptions.map((d, i) => (
                <div key={i} className="ab-variant-card" style={{ marginBottom: 6 }} data-testid="auto-meta-desc-variant">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span className="ai-suggest-type" style={{ fontSize: 9 }}>{d.style}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: scoreColor(d.score) }}>{d.score}</span>
                  </div>
                  <p style={{ fontSize: 11, marginBottom: 2 }}>"{d.text}"</p>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{d.length} znaków</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">AI wygeneruje zoptymalizowane meta title i meta description na podstawie treści artykułu.</p>
      )}
    </div>
  );
};

export default AutoMetaPanel;
