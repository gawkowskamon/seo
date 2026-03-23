import React, { useState, useCallback } from 'react';
import { Shield, Loader2, CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ScoreRing = ({ score, size = 80 }) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? '#16a34a' : score >= 50 ? '#f59e0b' : '#ef4444';

  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="var(--border)" strokeWidth="6" />
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="6"
        strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.6s ease' }} />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central"
        style={{ transform: 'rotate(90deg)', transformOrigin: 'center', fontSize: 18, fontWeight: 700, fill: color }}>
        {score}%
      </text>
    </svg>
  );
};

const PlagiarismPanel = ({ articleId }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/plagiarism/status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('Analiza plagiatu zakończona');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd analizy');
      } else {
        setTimeout(() => pollStatus(jobId), 2500);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const runCheck = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/plagiarism/check`, { article_id: articleId });
      if (res.data.job_id) {
        setTimeout(() => pollStatus(res.data.job_id), 2500);
      }
    } catch (err) {
      setLoading(false);
      toast.error('Błąd uruchamiania sprawdzania');
    }
  };

  const getVerdictInfo = (verdict) => {
    switch (verdict) {
      case 'oryginalny': return { icon: CheckCircle, color: '#16a34a', label: 'Oryginalny', bg: '#f0fdf4' };
      case 'podejrzany': return { icon: AlertTriangle, color: '#f59e0b', label: 'Podejrzany', bg: '#fffbeb' };
      default: return { icon: XCircle, color: '#ef4444', label: 'Prawdopodobny plagiat', bg: '#fef2f2' };
    }
  };

  return (
    <div className="plagiarism-panel" data-testid="plagiarism-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Sprawdzanie plagiatu</span>
        </div>
        <Button
          size="sm"
          onClick={runCheck}
          disabled={loading || !articleId}
          className="gap-1"
          data-testid="plagiarism-check-button"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Shield size={14} />}
          {loading ? 'Sprawdzam...' : 'Sprawdź'}
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>Analizuję oryginalność treści...</p>
        </div>
      )}

      {result && !loading && (
        <div className="plagiarism-result">
          {/* Score & Verdict */}
          <div className="plagiarism-score-row">
            <ScoreRing score={result.overall_score || 0} />
            <div>
              {(() => {
                const v = getVerdictInfo(result.verdict);
                return (
                  <div className="plagiarism-verdict" style={{ background: v.bg, color: v.color }}>
                    <v.icon size={16} /> {v.label}
                  </div>
                );
              })()}
              <p className="plagiarism-summary">{result.summary}</p>
            </div>
          </div>

          {/* Detail Bars */}
          {result.details && (
            <div className="plagiarism-details">
              <DetailBar label="Oryginalność" value={result.details.originality} />
              <DetailBar label="Unikalność stylu" value={result.details.style_uniqueness} />
              <DetailBar label="Ryzyko AI" value={100 - (result.details.ai_detection_risk || 0)} invert />
              <DetailBar label="Szablonowe frazy" value={100 - (result.details.template_phrases_detected || 0)} invert />
            </div>
          )}

          {/* Flagged Sections */}
          {result.flagged_sections?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => setShowDetails(!showDetails)} data-testid="plagiarism-toggle-details">
                {showDetails ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Oznaczone fragmenty ({result.flagged_sections.length})
              </button>
              {showDetails && result.flagged_sections.map((fs, idx) => (
                <div key={idx} className="plagiarism-flag-item" style={{
                  borderLeft: `3px solid ${fs.risk_level === 'wysoki' ? '#ef4444' : fs.risk_level === 'średni' ? '#f59e0b' : '#94a3b8'}`
                }}>
                  <p className="plagiarism-flag-text">"{fs.text?.substring(0, 120)}..."</p>
                  <p className="plagiarism-flag-reason">{fs.reason}</p>
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations?.length > 0 && (
            <div className="plagiarism-recs">
              <h4>Rekomendacje</h4>
              <ul>
                {result.recommendations.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">Kliknij "Sprawdź" aby przeanalizować oryginalność artykułu.</p>
      )}
    </div>
  );
};

const DetailBar = ({ label, value, invert }) => {
  const color = value >= 70 ? '#16a34a' : value >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div className="plagiarism-bar-item">
      <div className="plagiarism-bar-label">
        <span>{label}</span>
        <span style={{ fontWeight: 600, color }}>{value}%</span>
      </div>
      <div className="plagiarism-bar-track">
        <div className="plagiarism-bar-fill" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
};

export default PlagiarismPanel;
