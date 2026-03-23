import React, { useState, useCallback } from 'react';
import { CalendarClock, Loader2, Clock, Star, AlertTriangle, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SmartSchedulePanel = ({ articleId }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState({});

  const toggle = (key) => setExpanded(p => ({ ...p, [key]: !p[key] }));

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/smart-schedule/status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('Harmonogram wygenerowany');
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

  const runAnalysis = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/smart-schedule`, { article_id: articleId });
      if (res.data.job_id) setTimeout(() => pollStatus(res.data.job_id), 2500);
    } catch {
      setLoading(false);
      toast.error('Błąd uruchamiania');
    }
  };

  return (
    <div className="plagiarism-panel" data-testid="smart-schedule-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CalendarClock size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Harmonogram publikacji</span>
        </div>
        <Button size="sm" onClick={runAnalysis} disabled={loading || !articleId} className="gap-1" data-testid="smart-schedule-run-button">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <CalendarClock size={14} />}
          {loading ? 'Analizuję...' : 'Zaproponuj'}
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>AI analizuje optymalny czas publikacji...</p>
        </div>
      )}

      {result && !loading && (
        <div className="plagiarism-result" style={{ gap: 10, display: 'flex', flexDirection: 'column' }}>
          {/* Best slot */}
          {result.best_slot && (
            <div className="ab-winner-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <Star size={16} style={{ color: '#f59e0b' }} />
                <span style={{ fontWeight: 600, fontSize: 12, color: '#f59e0b' }}>NAJLEPSZY TERMIN</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <span style={{ fontSize: 22, fontWeight: 700, fontFamily: "'Instrument Serif', Georgia, serif", color: '#04389E' }}>
                  {result.best_slot.day} {result.best_slot.time}
                </span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{result.best_slot.reason}</p>
            </div>
          )}

          <p className="plagiarism-summary">{result.summary}</p>

          {/* All recommended slots */}
          {result.recommended_slots?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggle('slots')} data-testid="schedule-toggle-slots">
                {expanded.slots ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                <Clock size={13} style={{ marginRight: 2 }} /> Wszystkie rekomendowane terminy ({result.recommended_slots.length})
              </button>
              {expanded.slots && result.recommended_slots.map((s, i) => (
                <div key={i} className="verify-ref-item">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <span className="verify-ref-text">{s.day} o {s.time}</span>
                    <span style={{ fontSize: 14, fontWeight: 700, color: s.score >= 80 ? '#16a34a' : '#f59e0b' }}>{s.score}</span>
                  </div>
                  <p className="verify-ref-note">{s.reason}</p>
                </div>
              ))}
            </div>
          )}

          {/* Distribution plan */}
          {result.distribution_plan?.length > 0 && (
            <div className="plagiarism-flagged">
              <button className="plagiarism-toggle" onClick={() => toggle('dist')}>
                {expanded.dist ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Plan dystrybucji ({result.distribution_plan.length} kanałów)
              </button>
              {expanded.dist && result.distribution_plan.map((d, i) => (
                <div key={i} className="verify-ref-item">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                    <CheckCircle size={13} style={{ color: '#16a34a' }} />
                    <span className="verify-ref-text">{d.channel}</span>
                    <span className="verify-rec-area">{d.timing}</span>
                  </div>
                  <p className="verify-ref-note">{d.tip}</p>
                </div>
              ))}
            </div>
          )}

          {/* Seasonal notes */}
          {result.seasonal_notes && (
            <div className="verify-ref-item" style={{ borderLeft: '3px solid #f59e0b' }}>
              <span className="verify-ref-text" style={{ fontSize: 11 }}>Sezonowość</span>
              <p className="verify-ref-note">{result.seasonal_notes}</p>
            </div>
          )}

          {/* Avoid */}
          {result.avoid?.length > 0 && (
            <div className="plagiarism-recs">
              <h4><AlertTriangle size={13} style={{ display: 'inline', marginRight: 4, color: '#ef4444' }} />Unikaj</h4>
              <ul>
                {result.avoid.map((a, i) => <li key={i} style={{ color: '#ef4444' }}>{a}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">AI zaproponuje optymalny dzień i godzinę publikacji na WordPress na podstawie branży i treści artykułu.</p>
      )}
    </div>
  );
};

export default SmartSchedulePanel;
