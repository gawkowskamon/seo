import React, { useState, useEffect } from 'react';
import { Search, Loader2, AlertTriangle, CheckCircle2, XCircle, ExternalLink, BarChart3, Globe, Shield, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const STATUS_ICON = {
  ok: <CheckCircle2 size={14} style={{ color: 'hsl(142, 71%, 35%)' }} />,
  warning: <AlertTriangle size={14} style={{ color: 'hsl(38, 92%, 45%)' }} />,
  error: <XCircle size={14} style={{ color: 'hsl(0, 72%, 50%)' }} />
};

const GRADE_COLORS = {
  'A': { bg: 'hsl(142, 50%, 94%)', color: 'hsl(142, 71%, 30%)', border: 'hsl(142, 50%, 80%)' },
  'B': { bg: 'hsl(142, 40%, 94%)', color: 'hsl(142, 50%, 35%)', border: 'hsl(142, 40%, 80%)' },
  'C': { bg: 'hsl(38, 92%, 95%)', color: 'hsl(38, 70%, 35%)', border: 'hsl(38, 80%, 80%)' },
  'D': { bg: 'hsl(15, 90%, 95%)', color: 'hsl(15, 70%, 35%)', border: 'hsl(15, 80%, 80%)' },
  'F': { bg: 'hsl(0, 72%, 95%)', color: 'hsl(0, 72%, 35%)', border: 'hsl(0, 72%, 80%)' }
};

const ScoreBar = ({ score, label }) => (
  <div style={{ marginBottom: 12 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
      <span style={{ fontWeight: 600 }}>{label}</span>
      <span style={{ fontWeight: 700, color: score >= 70 ? 'hsl(142, 71%, 35%)' : score >= 50 ? 'hsl(38, 70%, 35%)' : 'hsl(0, 72%, 50%)' }}>{score}/100</span>
    </div>
    <div style={{ height: 6, borderRadius: 3, background: 'hsl(214, 18%, 90%)' }}>
      <div style={{
        height: '100%', borderRadius: 3, width: `${score}%`,
        background: score >= 70 ? 'hsl(142, 71%, 45%)' : score >= 50 ? 'hsl(38, 92%, 50%)' : 'hsl(0, 72%, 55%)',
        transition: 'width 0.5s ease'
      }} />
    </div>
  </div>
);

export default function SEOAuditPage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await axios.get(`${BACKEND_URL}/api/seo-audit/history`, { headers });
      setHistory(res.data || []);
    } catch (e) { /* ignore */ }
  };

  const handleAudit = async () => {
    if (!url) { toast.error('Podaj adres URL'); return; }
    setLoading(true);
    setResult(null);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      // Start async audit
      const startRes = await axios.post(`${BACKEND_URL}/api/seo-audit`, { url }, { headers });
      const jobId = startRes.data.job_id;
      
      // Poll for result
      const poll = async () => {
        const statusRes = await axios.get(`${BACKEND_URL}/api/seo-audit/status/${jobId}`, { headers });
        if (statusRes.data.status === 'completed') {
          setResult(statusRes.data.result);
          loadHistory();
          toast.success('Audyt SEO zakonczony');
          setLoading(false);
        } else if (statusRes.data.status === 'failed') {
          toast.error(statusRes.data.error || 'Blad audytu');
          setLoading(false);
        } else {
          setTimeout(poll, 2000);
        }
      };
      setTimeout(poll, 2000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad audytu');
      setLoading(false);
    }
  };

  const gradeStyle = result?.grade ? (GRADE_COLORS[result.grade] || GRADE_COLORS['C']) : {};

  return (
    <div className="page-container" data-testid="seo-audit-page">
      <div className="page-header">
        <div>
          <h1>Audyt SEO</h1>
          <p style={{ fontSize: 14, color: 'hsl(215, 16%, 45%)', marginTop: 4 }}>
            Przeskanuj dowolna strone i otrzymaj rekomendacje AI
          </p>
        </div>
      </div>

      <div style={{
        background: 'white', borderRadius: 16, padding: 24,
        border: '1px solid hsl(214, 18%, 88%)', marginBottom: 24
      }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Input value={url} onChange={(e) => setUrl(e.target.value)}
            placeholder="https://twoja-strona.pl" data-testid="audit-url-input"
            style={{ flex: 1 }} onKeyDown={(e) => e.key === 'Enter' && handleAudit()} />
          <Button onClick={handleAudit} disabled={loading} className="gap-2" data-testid="audit-run-btn">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            {loading ? 'Skanowanie...' : 'Audytuj'}
          </Button>
        </div>
      </div>

      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 20 }}>
          {/* Left: Score overview */}
          <div>
            <div style={{
              background: gradeStyle.bg || 'white', borderRadius: 16, padding: 24,
              border: `1px solid ${gradeStyle.border || 'hsl(214, 18%, 88%)'}`,
              textAlign: 'center', marginBottom: 16
            }} data-testid="audit-score-card">
              <div style={{
                fontSize: 48, fontWeight: 800, color: gradeStyle.color || '#04389E',
                fontFamily: "'Instrument Serif', Georgia, serif"
              }}>
                {result.overall_score}
              </div>
              <div style={{
                display: 'inline-block', padding: '4px 16px', borderRadius: 20,
                background: gradeStyle.color || '#04389E', color: 'white',
                fontWeight: 700, fontSize: 18, marginTop: 4
              }}>
                {result.grade}
              </div>
            </div>
            <div style={{
              background: 'white', borderRadius: 16, padding: 20,
              border: '1px solid hsl(214, 18%, 88%)'
            }}>
              <ScoreBar score={result.on_page_seo?.score || 0} label="On-Page SEO" />
              <ScoreBar score={result.content_analysis?.score || 0} label="Tresc" />
              <ScoreBar score={result.technical_seo?.score || 0} label="Techniczne SEO" />
            </div>
            {result.scraped_data && (
              <div style={{
                background: 'white', borderRadius: 16, padding: 16, marginTop: 16,
                border: '1px solid hsl(214, 18%, 88%)', fontSize: 12
              }}>
                <h4 style={{ fontWeight: 600, marginBottom: 8, fontSize: 13 }}>Dane strony</h4>
                {Object.entries({
                  'Tytul': result.scraped_data.title?.substring(0, 50),
                  'Slow': result.scraped_data.word_count,
                  'H1': result.scraped_data.h1_count,
                  'H2': result.scraped_data.h2_count,
                  'Obrazki': result.scraped_data.images_total,
                  'Linki wewn.': result.scraped_data.internal_links,
                  'Linki zewn.': result.scraped_data.external_links
                }).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', borderBottom: '1px solid hsl(214, 18%, 95%)' }}>
                    <span style={{ color: 'hsl(215, 16%, 50%)' }}>{k}</span>
                    <span style={{ fontWeight: 600 }}>{v}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: Findings */}
          <div>
            {result.summary && (
              <div style={{
                background: 'hsl(220, 95%, 96%)', borderRadius: 12, padding: '14px 20px',
                marginBottom: 16, fontSize: 14, color: '#04389E', lineHeight: 1.5,
                border: '1px solid hsl(220, 70%, 90%)'
              }}>
                {result.summary}
              </div>
            )}

            {(result.critical_issues || []).length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: 'hsl(0, 72%, 40%)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <AlertTriangle size={16} /> Krytyczne problemy
                </h3>
                {result.critical_issues.map((issue, i) => (
                  <div key={i} style={{
                    background: 'hsl(0, 72%, 97%)', borderRadius: 10, padding: '12px 16px',
                    border: '1px solid hsl(0, 50%, 90%)', marginBottom: 8
                  }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{issue.issue}</div>
                    <div style={{ fontSize: 12, color: 'hsl(0, 40%, 40%)', marginTop: 4 }}>{issue.recommendation}</div>
                  </div>
                ))}
              </div>
            )}

            {['on_page_seo', 'content_analysis', 'technical_seo'].map((category) => {
              const data = result[category];
              if (!data?.findings?.length) return null;
              const labels = { on_page_seo: 'On-Page SEO', content_analysis: 'Analiza tresci', technical_seo: 'Techniczne SEO' };
              const icons = { on_page_seo: <Globe size={15} />, content_analysis: <FileText size={15} />, technical_seo: <Shield size={15} /> };
              return (
                <div key={category} style={{ marginBottom: 20 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6, color: 'hsl(222, 47%, 11%)' }}>
                    {icons[category]} {labels[category]}
                  </h3>
                  <div style={{ background: 'white', borderRadius: 12, border: '1px solid hsl(214, 18%, 88%)', overflow: 'hidden' }}>
                    {data.findings.map((f, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 16px',
                        borderBottom: i < data.findings.length - 1 ? '1px solid hsl(214, 18%, 93%)' : 'none'
                      }}>
                        {STATUS_ICON[f.status]}
                        <div style={{ flex: 1, fontSize: 13 }}>
                          <span style={{ fontWeight: 600 }}>{f.item}</span>
                          <span style={{ color: 'hsl(215, 16%, 50%)', marginLeft: 6 }}>{f.detail}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            {(result.recommendations || []).length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <BarChart3 size={15} /> Rekomendacje
                </h3>
                {result.recommendations.map((r, i) => (
                  <div key={i} style={{
                    background: 'white', borderRadius: 10, padding: '12px 16px',
                    border: '1px solid hsl(214, 18%, 88%)', marginBottom: 8
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{
                        fontSize: 10, padding: '2px 8px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase',
                        background: r.priority === 'wysoki' ? 'hsl(0, 72%, 95%)' : r.priority === 'sredni' ? 'hsl(38, 92%, 95%)' : 'hsl(210, 33%, 96%)',
                        color: r.priority === 'wysoki' ? 'hsl(0, 72%, 40%)' : r.priority === 'sredni' ? 'hsl(38, 70%, 35%)' : 'hsl(210, 30%, 40%)'
                      }}>
                        {r.priority}
                      </span>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{r.title}</span>
                    </div>
                    <p style={{ fontSize: 12, color: 'hsl(215, 16%, 40%)', margin: 0 }}>{r.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {!result && history.length > 0 && (
        <div style={{ background: 'white', borderRadius: 16, padding: 20, border: '1px solid hsl(214, 18%, 88%)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Historia audytow</h3>
          {history.map((h) => (
            <div key={h.id} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 0', borderBottom: '1px solid hsl(214, 18%, 93%)'
            }}>
              <div>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{h.url}</span>
                <span style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', marginLeft: 12 }}>
                  {h.created_at ? new Date(h.created_at).toLocaleDateString('pl-PL') : ''}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>{h.result?.overall_score || '?'}</span>
                <span style={{
                  padding: '2px 8px', borderRadius: 6, fontWeight: 700, fontSize: 12,
                  ...(GRADE_COLORS[h.result?.grade] || {})
                }}>
                  {h.result?.grade || '?'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
