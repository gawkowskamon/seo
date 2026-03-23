import React, { useState, useCallback } from 'react';
import { FlaskConical, Loader2, Trophy, Star, ArrowRight, Plus, X } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ScoreBar = ({ label, value, color }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11 }}>
    <span style={{ minWidth: 50, color: 'var(--text-secondary)' }}>{label}</span>
    <div style={{ flex: 1, height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
      <div style={{ width: `${value}%`, height: '100%', background: color || 'var(--accent)', borderRadius: 3, transition: 'width 0.4s ease' }} />
    </div>
    <span style={{ minWidth: 24, fontWeight: 600, fontSize: 11, color }}>{value}</span>
  </div>
);

const totalColor = (t) => t >= 80 ? '#16a34a' : t >= 60 ? '#f59e0b' : '#ef4444';

const ABTitleTestPanel = ({ articleId, currentTitle, onApplyTitle }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [customVariants, setCustomVariants] = useState([]);
  const [newVariant, setNewVariant] = useState('');

  const addVariant = () => {
    if (newVariant.trim() && customVariants.length < 3) {
      setCustomVariants([...customVariants, newVariant.trim()]);
      setNewVariant('');
    }
  };

  const removeVariant = (idx) => {
    setCustomVariants(customVariants.filter((_, i) => i !== idx));
  };

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/ab-title-status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('A/B test tytułów zakończony');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd testu');
      } else {
        setTimeout(() => pollStatus(jobId), 2000);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const runTest = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/ab-title-test`, {
        article_id: articleId,
        custom_variants: customVariants
      });
      if (res.data.job_id) {
        setTimeout(() => pollStatus(res.data.job_id), 2500);
      }
    } catch (err) {
      setLoading(false);
      toast.error('Błąd uruchamiania testu');
    }
  };

  const handleApply = (text) => {
    if (onApplyTitle) {
      onApplyTitle(text);
      toast.success('Tytuł zastosowany');
    }
  };

  return (
    <div className="plagiarism-panel" data-testid="ab-title-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <FlaskConical size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>A/B Test tytułów</span>
        </div>
        <Button size="sm" onClick={runTest} disabled={loading || !articleId} className="gap-1" data-testid="ab-title-run-button">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
          {loading ? 'Testuję...' : 'Testuj'}
        </Button>
      </div>

      {/* Custom variants input */}
      {!loading && !result && (
        <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)' }}>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6 }}>Dodaj własne warianty (opcjonalnie, max 3):</p>
          <div style={{ display: 'flex', gap: 6 }}>
            <Input
              value={newVariant}
              onChange={(e) => setNewVariant(e.target.value)}
              placeholder="Twój wariant tytułu..."
              style={{ fontSize: 12, height: 30 }}
              onKeyDown={(e) => e.key === 'Enter' && addVariant()}
              data-testid="ab-title-custom-input"
            />
            <Button size="sm" variant="outline" onClick={addVariant} disabled={!newVariant.trim() || customVariants.length >= 3} style={{ height: 30, minWidth: 30, padding: '0 8px' }}>
              <Plus size={14} />
            </Button>
          </div>
          {customVariants.map((v, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4, padding: '3px 8px', background: 'var(--bg-muted)', borderRadius: 4, fontSize: 11 }}>
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v}</span>
              <button onClick={() => removeVariant(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 2 }}>
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>AI generuje i ocenia warianty tytułów...</p>
        </div>
      )}

      {result && !loading && (
        <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Winner */}
          {result.winner && (
            <div className="ab-winner-card" data-testid="ab-title-winner">
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Trophy size={16} style={{ color: '#f59e0b' }} />
                <span style={{ fontWeight: 600, fontSize: 12, color: '#f59e0b' }}>ZWYCIĘZCA</span>
                <span style={{ fontSize: 18, fontWeight: 700, color: totalColor(result.winner.total), marginLeft: 'auto' }}>{result.winner.total}</span>
              </div>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>"{result.winner.text}"</p>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6 }}>{result.winner.reason}</p>
              {result.winner.text !== currentTitle && (
                <Button size="sm" className="gap-1 w-full" onClick={() => handleApply(result.winner.text)} data-testid="ab-title-apply-winner">
                  Zastosuj ten tytuł <ArrowRight size={14} />
                </Button>
              )}
            </div>
          )}

          {/* Current title */}
          {result.current_title && (
            <div className="ab-variant-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Obecny tytuł</span>
                <span style={{ fontSize: 16, fontWeight: 700, color: totalColor(result.current_title.total) }}>{result.current_title.total}</span>
              </div>
              <p style={{ fontSize: 12, fontWeight: 500, marginBottom: 6 }}>"{result.current_title.text}"</p>
              <ScoreBar label="CTR" value={result.current_title.scores?.ctr || 0} color="#04389E" />
              <ScoreBar label="SEO" value={result.current_title.scores?.seo || 0} color="#16a34a" />
              <ScoreBar label="Emocje" value={result.current_title.scores?.emotion || 0} color="#f59e0b" />
              <ScoreBar label="Jasność" value={result.current_title.scores?.clarity || 0} color="#8b5cf6" />
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6 }}>{result.current_title.feedback}</p>
            </div>
          )}

          {/* Variants */}
          {result.variants?.map((v, idx) => (
            <div key={idx} className="ab-variant-card" data-testid="ab-title-variant">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Wariant {idx + 1}</span>
                  {v.strategy && <span className="ai-suggest-type" style={{ fontSize: 9 }}>{v.strategy}</span>}
                </div>
                <span style={{ fontSize: 16, fontWeight: 700, color: totalColor(v.total) }}>{v.total}</span>
              </div>
              <p style={{ fontSize: 12, fontWeight: 500, marginBottom: 4 }}>"{v.text}"</p>
              <ScoreBar label="CTR" value={v.scores?.ctr || 0} color="#04389E" />
              <ScoreBar label="SEO" value={v.scores?.seo || 0} color="#16a34a" />
              <ScoreBar label="Emocje" value={v.scores?.emotion || 0} color="#f59e0b" />
              <ScoreBar label="Jasność" value={v.scores?.clarity || 0} color="#8b5cf6" />
              {v.changes_made && <p style={{ fontSize: 10, color: 'var(--accent)', marginTop: 4 }}>{v.changes_made}</p>}
              {v.text !== currentTitle && (
                <Button size="sm" variant="outline" className="gap-1 w-full" style={{ marginTop: 6, height: 28, fontSize: 11 }} onClick={() => handleApply(v.text)} data-testid="ab-title-apply-variant">
                  Zastosuj <ArrowRight size={12} />
                </Button>
              )}
            </div>
          ))}

          {/* Tips */}
          {result.tips?.length > 0 && (
            <div className="plagiarism-recs" style={{ marginTop: 4 }}>
              <h4><Star size={13} style={{ display: 'inline', marginRight: 4 }} />Porady</h4>
              <ul>
                {result.tips.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">AI wygeneruje warianty tytułu i oceni je pod kątem CTR, SEO, emocji i jasności.</p>
      )}
    </div>
  );
};

export default ABTitleTestPanel;
