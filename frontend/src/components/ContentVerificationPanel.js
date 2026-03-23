import React, { useState, useCallback } from 'react';
import { FileCheck, Loader2, CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp, Scale, BookOpen, Database, AlertOctagon } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const StatusIcon = ({ status }) => {
  switch (status) {
    case 'poprawny': case 'poprawne': return <CheckCircle size={13} style={{ color: '#16a34a' }} />;
    case 'nieaktualny': case 'nieaktualne': case 'nieprecyzyjne': return <AlertTriangle size={13} style={{ color: '#f59e0b' }} />;
    case 'błędny': case 'błędne': return <XCircle size={13} style={{ color: '#ef4444' }} />;
    default: return <AlertTriangle size={13} style={{ color: '#94a3b8' }} />;
  }
};

const ScoreBar = ({ label, icon: Icon, score }) => {
  const color = score >= 70 ? '#16a34a' : score >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div className="verify-score-bar">
      <div className="verify-score-bar-header">
        <span><Icon size={13} /> {label}</span>
        <span style={{ fontWeight: 600, color }}>{score}%</span>
      </div>
      <div className="plagiarism-bar-track">
        <div className="plagiarism-bar-fill" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
};

const ContentVerificationPanel = ({ articleId }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState({});

  const toggleSection = (key) => setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }));

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/verify/status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('Weryfikacja zakończona');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd weryfikacji');
      } else {
        setTimeout(() => pollStatus(jobId), 2500);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const runVerification = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/verify/check`, { article_id: articleId });
      if (res.data.job_id) {
        setTimeout(() => pollStatus(res.data.job_id), 3000);
      }
    } catch (err) {
      setLoading(false);
      toast.error('Błąd uruchamiania weryfikacji');
    }
  };

  const getVerdictInfo = (verdict) => {
    switch (verdict) {
      case 'rzetelny': return { icon: CheckCircle, color: '#16a34a', bg: '#f0fdf4', label: 'Rzetelny' };
      case 'wymaga poprawek': return { icon: AlertTriangle, color: '#f59e0b', bg: '#fffbeb', label: 'Wymaga poprawek' };
      default: return { icon: XCircle, color: '#ef4444', bg: '#fef2f2', label: 'Nierzetelny' };
    }
  };

  const priorityColor = (p) => p === 'wysoki' ? '#ef4444' : p === 'średni' ? '#f59e0b' : '#94a3b8';

  return (
    <div className="plagiarism-panel" data-testid="verification-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <FileCheck size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Weryfikacja treści</span>
        </div>
        <Button size="sm" onClick={runVerification} disabled={loading || !articleId} className="gap-1" data-testid="verification-check-button">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <FileCheck size={14} />}
          {loading ? 'Weryfikuję...' : 'Weryfikuj'}
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>AI weryfikuje rzetelność treści, przepisy i dane...</p>
        </div>
      )}

      {result && !loading && (
        <div className="plagiarism-result" style={{ gap: 10, display: 'flex', flexDirection: 'column' }}>
          {/* Overall verdict */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "'Instrument Serif', Georgia, serif", color: (result.overall_reliability_score || 0) >= 70 ? '#16a34a' : '#f59e0b' }}>
              {result.overall_reliability_score || 0}%
            </div>
            <div>
              {(() => {
                const v = getVerdictInfo(result.verdict);
                return (
                  <div className="plagiarism-verdict" style={{ background: v.bg, color: v.color }}>
                    <v.icon size={14} /> {v.label}
                  </div>
                );
              })()}
              <p className="plagiarism-summary">{result.summary}</p>
            </div>
          </div>

          {/* Score bars */}
          <div className="plagiarism-details">
            <ScoreBar label="Zgodność prawna" icon={Scale} score={result.legal_accuracy?.score || 0} />
            <ScoreBar label="Poprawność faktów" icon={BookOpen} score={result.factual_accuracy?.score || 0} />
            <ScoreBar label="Kompletność" icon={Database} score={result.completeness?.score || 0} />
            <ScoreBar label="Jakość źródeł" icon={AlertOctagon} score={result.sources_quality?.score || 0} />
          </div>

          {/* Legal references */}
          {result.legal_accuracy?.verified_references?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggleSection('legal')} data-testid="verification-toggle-legal">
                {expandedSections.legal ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Przepisy prawne ({result.legal_accuracy.verified_references.length})
              </button>
              {expandedSections.legal && result.legal_accuracy.verified_references.map((ref, idx) => (
                <div key={idx} className="verify-ref-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <StatusIcon status={ref.status} />
                    <span className="verify-ref-text">{ref.reference}</span>
                    <span className={`verify-status-badge verify-status-${ref.status === 'poprawny' ? 'ok' : ref.status === 'nieaktualny' ? 'warn' : 'err'}`}>
                      {ref.status}
                    </span>
                  </div>
                  {ref.note && <p className="verify-ref-note">{ref.note}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Factual accuracy */}
          {result.factual_accuracy?.verified_facts?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggleSection('facts')} data-testid="verification-toggle-facts">
                {expandedSections.facts ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Weryfikacja faktów ({result.factual_accuracy.verified_facts.length})
              </button>
              {expandedSections.facts && result.factual_accuracy.verified_facts.map((fact, idx) => (
                <div key={idx} className="verify-ref-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <StatusIcon status={fact.status} />
                    <span className="verify-ref-text">{fact.claim}</span>
                  </div>
                  {fact.correction && <p className="verify-ref-note" style={{ color: '#ef4444' }}>Korekta: {fact.correction}</p>}
                  {fact.source && <p className="verify-ref-note">Źródło: {fact.source}</p>}
                </div>
              ))}
            </div>
          )}

          {/* Missing info */}
          {(result.completeness?.missing_info?.length > 0 || result.completeness?.missing_disclaimers?.length > 0) && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggleSection('missing')} data-testid="verification-toggle-missing">
                {expandedSections.missing ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Brakujące informacje
              </button>
              {expandedSections.missing && (
                <>
                  {result.completeness.missing_info?.map((m, i) => (
                    <div key={i} className="verify-ref-item" style={{ borderLeft: '3px solid #f59e0b' }}>
                      <p className="verify-ref-text">{m}</p>
                    </div>
                  ))}
                  {result.completeness.missing_disclaimers?.map((d, i) => (
                    <div key={`d-${i}`} className="verify-ref-item" style={{ borderLeft: '3px solid #ef4444' }}>
                      <p className="verify-ref-text" style={{ color: '#ef4444' }}>Brak disclaimera: {d}</p>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations?.length > 0 && (
            <div className="plagiarism-recs">
              <h4>Rekomendacje poprawy</h4>
              {result.recommendations.map((r, idx) => (
                <div key={idx} className="verify-rec-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                    <span className="verify-rec-priority" style={{ color: priorityColor(r.priority) }}>{r.priority}</span>
                    <span className="verify-rec-area">{r.area}</span>
                  </div>
                  <p className="verify-rec-desc">{r.description}</p>
                  {r.suggested_text && <p className="verify-rec-suggestion">"{r.suggested_text}"</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">Kliknij "Weryfikuj" aby sprawdzić rzetelność treści, przepisy prawne i dane faktyczne.</p>
      )}
    </div>
  );
};

export default ContentVerificationPanel;
