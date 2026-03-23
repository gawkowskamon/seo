import React, { useState, useCallback } from 'react';
import { Search, Loader2, TrendingUp, AlertTriangle, CheckCircle, ChevronDown, ChevronUp, ExternalLink, Target, Zap } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PriorityBadge = ({ priority }) => {
  const c = priority === 'wysoka' ? '#ef4444' : priority === 'średnia' ? '#f59e0b' : '#94a3b8';
  return <span style={{ fontSize: 10, fontWeight: 600, color: c, textTransform: 'uppercase' }}>{priority}</span>;
};

const AutoCompetitionPanel = ({ articleId }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState({});

  const toggle = (key) => setExpanded(p => ({ ...p, [key]: !p[key] }));

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/competition/auto-status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('Analiza konkurencji zakończona');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd analizy');
      } else {
        setTimeout(() => pollStatus(jobId), 3000);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const runAnalysis = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/competition/auto-analyze`, { article_id: articleId });
      if (res.data.job_id) {
        setTimeout(() => pollStatus(res.data.job_id), 3000);
      }
    } catch (err) {
      setLoading(false);
      toast.error('Błąd uruchamiania analizy');
    }
  };

  const posColor = (p) => p === 'silniejszy' ? '#16a34a' : p === 'porównywalny' ? '#f59e0b' : '#ef4444';

  return (
    <div className="plagiarism-panel" data-testid="auto-competition-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Search size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Analiza konkurencji</span>
        </div>
        <Button size="sm" onClick={runAnalysis} disabled={loading || !articleId} className="gap-1" data-testid="auto-competition-run-button">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          {loading ? 'Analizuję...' : 'Analizuj'}
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>Szukam i analizuję top wyniki Google...</p>
          <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>To może potrwać 15-30 sekund</p>
        </div>
      )}

      {result && !loading && (
        <div className="plagiarism-result" style={{ gap: 10, display: 'flex', flexDirection: 'column' }}>
          {/* Position verdict */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingBottom: 8, borderBottom: '1px solid var(--border-light)' }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: posColor(result.overall_position) }}>
              {result.overall_position === 'silniejszy' ? <CheckCircle size={16} style={{ display: 'inline', marginRight: 4 }} /> : <AlertTriangle size={16} style={{ display: 'inline', marginRight: 4 }} />}
              Twoja pozycja: {result.overall_position}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              ({result.competitors_found || 0} konkurentów)
            </span>
          </div>

          <p className="plagiarism-summary">{result.summary}</p>

          {/* Competitors scraped */}
          {result.competitors_scraped?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggle('comp')} data-testid="competition-toggle-competitors">
                {expanded.comp ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Znalezione konkurencyjne artykuły ({result.competitors_scraped.length})
              </button>
              {expanded.comp && result.competitors_scraped.map((c, i) => (
                <div key={i} className="verify-ref-item">
                  <a href={c.url} target="_blank" rel="noopener noreferrer" className="verify-ref-text" style={{ color: 'var(--accent)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    {c.title?.substring(0, 60) || c.url} <ExternalLink size={11} />
                  </a>
                  <span className="verify-ref-note">~{c.word_count} słów</span>
                </div>
              ))}
            </div>
          )}

          {/* Content gaps */}
          {result.content_gaps?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggle('gaps')} data-testid="competition-toggle-gaps">
                {expanded.gaps ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                <Target size={13} style={{ marginRight: 2 }} /> Luki w treści ({result.content_gaps.length})
              </button>
              {expanded.gaps && result.content_gaps.map((g, i) => (
                <div key={i} className="verify-ref-item" style={{ borderLeft: `3px solid ${g.importance === 'wysoka' ? '#ef4444' : g.importance === 'średnia' ? '#f59e0b' : '#94a3b8'}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <span className="verify-ref-text">{g.topic}</span>
                    <PriorityBadge priority={g.importance} />
                  </div>
                  <p className="verify-ref-note">{g.suggestion}</p>
                  {g.suggested_heading && <p className="verify-rec-suggestion">H2/H3: "{g.suggested_heading}"</p>}
                </div>
              ))}
            </div>
          )}

          {/* Keyword opportunities */}
          {result.keyword_opportunities?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggle('kw')} data-testid="competition-toggle-keywords">
                {expanded.kw ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Możliwości keyword ({result.keyword_opportunities.length})
              </button>
              {expanded.kw && result.keyword_opportunities.map((k, i) => (
                <div key={i} className="verify-ref-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span className="verify-ref-text">{k.keyword}</span>
                    <span className="verify-ref-note" style={{ display: 'block' }}>{k.my_usage}</span>
                  </div>
                  <span className={`verify-status-badge ${k.action === 'Dodaj' ? 'verify-status-err' : k.action === 'Wzmocnij' ? 'verify-status-warn' : 'verify-status-ok'}`}>
                    {k.action}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Structural comparison */}
          {result.structural_comparison && (
            <div className="verify-ref-item" style={{ background: 'var(--bg-muted)' }}>
              <span className="verify-ref-text" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Porównanie struktury</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 11 }}>
                <div>Twoje sekcje: <strong>{result.structural_comparison.my_sections}</strong></div>
                <div>Śr. konkurencji: <strong>{result.structural_comparison.avg_competitor_sections}</strong></div>
                <div>Twoje słowa: <strong>{result.structural_comparison.my_word_count}</strong></div>
                <div>Śr. konkurencji: <strong>{result.structural_comparison.avg_competitor_word_count}</strong></div>
              </div>
              {result.structural_comparison.recommendation && (
                <p className="verify-ref-note" style={{ marginTop: 4 }}>{result.structural_comparison.recommendation}</p>
              )}
            </div>
          )}

          {/* Action plan */}
          {result.action_plan?.length > 0 && (
            <div className="plagiarism-recs">
              <h4><Zap size={13} style={{ display: 'inline', marginRight: 4 }} />Plan działania</h4>
              {result.action_plan.map((a, i) => (
                <div key={i} className="verify-rec-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)' }}>#{a.priority}</span>
                    <span className="verify-rec-desc">{a.action}</span>
                  </div>
                  <span className={`verify-status-badge ${a.expected_impact === 'wysoki' ? 'verify-status-err' : 'verify-status-warn'}`} style={{ marginTop: 3, display: 'inline-block' }}>
                    wpływ: {a.expected_impact}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Strengths / Weaknesses */}
          {(result.strengths?.length > 0 || result.weaknesses?.length > 0) && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggle('sw')}>
                {expanded.sw ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Mocne i słabe strony
              </button>
              {expanded.sw && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <div>
                    {result.strengths?.map((s, i) => (
                      <div key={i} className="verify-ref-item" style={{ borderLeft: '3px solid #16a34a' }}>
                        <span className="verify-ref-note" style={{ color: '#16a34a' }}>{s}</span>
                      </div>
                    ))}
                  </div>
                  <div>
                    {result.weaknesses?.map((w, i) => (
                      <div key={i} className="verify-ref-item" style={{ borderLeft: '3px solid #ef4444' }}>
                        <span className="verify-ref-note" style={{ color: '#ef4444' }}>{w}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">Kliknij "Analizuj" aby porównać artykuł z top wynikami Google dla Twojego słowa kluczowego.</p>
      )}
    </div>
  );
};

export default AutoCompetitionPanel;
