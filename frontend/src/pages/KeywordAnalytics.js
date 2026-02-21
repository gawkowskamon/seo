import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, TrendingDown, Minus, Loader2, BarChart3, Target, Zap, Plus, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TrendBadge = ({ trend }) => {
  const config = {
    'rosnący': { icon: TrendingUp, color: '#10B981', bg: 'rgba(16,185,129,0.1)', label: 'Rosnący' },
    'malejący': { icon: TrendingDown, color: '#EF4444', bg: 'rgba(239,68,68,0.1)', label: 'Malejący' },
    'stabilny': { icon: Minus, color: '#F59E0B', bg: 'rgba(245,158,11,0.1)', label: 'Stabilny' },
  };
  const c = config[trend] || config['stabilny'];
  const Icon = c.icon;
  return (
    <span data-testid={`trend-badge-${trend}`} style={{
      display: 'inline-flex', alignItems: 'center', gap: 4, padding: '3px 8px',
      borderRadius: 6, fontSize: 11, fontWeight: 600, color: c.color, background: c.bg
    }}>
      <Icon size={12} /> {c.label}
    </span>
  );
};

const MiniChart = ({ data = [], color = '#04389E' }) => {
  if (!data.length) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const h = 32;
  const w = 80;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ');
  return (
    <svg width={w} height={h} style={{ display: 'block' }}>
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

const OpportunityBar = ({ score }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
    <div style={{ width: 60, height: 6, borderRadius: 3, background: 'var(--bg-hover)', overflow: 'hidden' }}>
      <div style={{
        width: `${score}%`, height: '100%', borderRadius: 3,
        background: score >= 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444',
        transition: 'width 0.5s'
      }} />
    </div>
    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>{score}</span>
  </div>
);

export default function KeywordAnalytics() {
  const [keywords, setKeywords] = useState([]);
  const [inputKw, setInputKw] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${BACKEND_URL}/api/keyword-analytics/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(res.data || []);
    } catch (e) {}
  };

  const addKeyword = () => {
    const kw = inputKw.trim();
    if (kw && !keywords.includes(kw) && keywords.length < 10) {
      setKeywords(prev => [...prev, kw]);
      setInputKw('');
    }
  };

  const removeKeyword = (kw) => setKeywords(prev => prev.filter(k => k !== kw));

  const handleAnalyze = async () => {
    setLoading(true);
    setResults(null);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const startRes = await axios.post(`${BACKEND_URL}/api/keyword-analytics/analyze`,
        { keywords, industry: 'rachunkowość i podatki' }, { headers });
      const jobId = startRes.data.job_id;

      const poll = async () => {
        const statusRes = await axios.get(`${BACKEND_URL}/api/keyword-analytics/status/${jobId}`, { headers });
        if (statusRes.data.status === 'completed') {
          setResults(statusRes.data.result);
          loadHistory();
          toast.success('Analiza słów kluczowych zakończona');
          setLoading(false);
        } else if (statusRes.data.status === 'failed') {
          toast.error(statusRes.data.error || 'Błąd analizy');
          setLoading(false);
        } else {
          setTimeout(poll, 2000);
        }
      };
      setTimeout(poll, 2000);
    } catch (err) {
      toast.error('Błąd analizy słów kluczowych');
      setLoading(false);
    }
  };

  const kwData = results?.keywords || [];

  return (
    <div data-testid="keyword-analytics-page" style={{ padding: '32px 40px', maxWidth: 1200 }}>
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 6 }}>
          Analityka słów kluczowych
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          Trendy, trudność i szanse pozycjonowania dla branży podatkowej
        </p>
      </div>

      {/* Input section */}
      <div data-testid="keyword-input-section" style={{
        background: 'var(--bg-card)', borderRadius: 14, padding: 24, marginBottom: 24,
        border: '1px solid var(--border)'
      }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input
            value={inputKw}
            onChange={(e) => setInputKw(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
            placeholder="Wpisz słowo kluczowe..."
            data-testid="keyword-input"
            style={{
              flex: 1, padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border)',
              fontSize: 14, background: 'var(--bg-input)', color: 'var(--text-primary)', outline: 'none'
            }}
          />
          <Button onClick={addKeyword} variant="outline" data-testid="add-keyword-btn">
            <Plus size={16} />
          </Button>
          <Button onClick={handleAnalyze} disabled={loading} data-testid="analyze-keywords-btn">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            <span style={{ marginLeft: 6 }}>Analizuj</span>
          </Button>
        </div>
        {keywords.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {keywords.map(kw => (
              <span key={kw} style={{
                display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                borderRadius: 8, fontSize: 12, fontWeight: 500, background: 'var(--bg-hover)',
                color: 'var(--text-primary)', border: '1px solid var(--border)'
              }}>
                {kw}
                <X size={12} style={{ cursor: 'pointer', opacity: 0.5 }} onClick={() => removeKeyword(kw)} />
              </span>
            ))}
          </div>
        )}
        {keywords.length === 0 && !loading && (
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
            Dodaj słowa kluczowe lub kliknij "Analizuj" aby użyć domyślnych fraz podatkowych
          </p>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{
          background: 'var(--bg-card)', borderRadius: 14, padding: 48, textAlign: 'center',
          border: '1px solid var(--border)'
        }}>
          <Loader2 size={32} className="animate-spin" style={{ color: 'var(--accent)', marginBottom: 12 }} />
          <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Analizuję słowa kluczowe...</p>
        </div>
      )}

      {/* Results */}
      {kwData.length > 0 && (
        <>
          {/* Summary cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
            <div style={{
              background: 'var(--bg-card)', borderRadius: 14, padding: 20, border: '1px solid var(--border)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <BarChart3 size={18} style={{ color: 'var(--accent)' }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>ŚR. WYSZUKIWAŃ</span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)' }}>
                {Math.round(kwData.reduce((s, k) => s + (k.monthly_searches || 0), 0) / kwData.length).toLocaleString('pl-PL')}
              </div>
            </div>
            <div style={{
              background: 'var(--bg-card)', borderRadius: 14, padding: 20, border: '1px solid var(--border)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Target size={18} style={{ color: '#F59E0B' }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>ŚR. TRUDNOŚĆ</span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)' }}>
                {Math.round(kwData.reduce((s, k) => s + (k.difficulty || 0), 0) / kwData.length)}
              </div>
            </div>
            <div style={{
              background: 'var(--bg-card)', borderRadius: 14, padding: 20, border: '1px solid var(--border)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Zap size={18} style={{ color: '#10B981' }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>NAJLEPSZA SZANSA</span>
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                {kwData.sort((a, b) => (b.opportunity_score || 0) - (a.opportunity_score || 0))[0]?.keyword || '-'}
              </div>
            </div>
          </div>

          {/* Table */}
          <div data-testid="keyword-results-table" style={{
            background: 'var(--bg-card)', borderRadius: 14, overflow: 'hidden',
            border: '1px solid var(--border)'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Słowo kluczowe', 'Wyszukiwania/msc', 'Trudność', 'Trend', '6 msc', 'CPC', 'Szansa'].map(h => (
                    <th key={h} style={{
                      padding: '12px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700,
                      color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em'
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {kwData.map((kw, i) => (
                  <tr key={i} style={{
                    borderBottom: '1px solid var(--border)',
                    transition: 'background 0.12s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)', marginBottom: 2 }}>
                        {kw.keyword}
                      </div>
                      {kw.related_topics?.length > 0 && (
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {kw.related_topics.slice(0, 2).map((t, j) => (
                            <span key={j} style={{
                              fontSize: 10, padding: '1px 6px', borderRadius: 4,
                              background: 'var(--bg-muted)', color: 'var(--text-secondary)'
                            }}>{t}</span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {(kw.monthly_searches || 0).toLocaleString('pl-PL')}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span style={{
                        fontSize: 12, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                        background: kw.difficulty > 70 ? 'rgba(239,68,68,0.1)' : kw.difficulty > 40 ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)',
                        color: kw.difficulty > 70 ? '#EF4444' : kw.difficulty > 40 ? '#F59E0B' : '#10B981'
                      }}>{kw.difficulty}</span>
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <TrendBadge trend={kw.trend} />
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <MiniChart data={kw.trend_data} color={kw.trend === 'rosnący' ? '#10B981' : kw.trend === 'malejący' ? '#EF4444' : '#F59E0B'} />
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: 'var(--text-primary)' }}>
                      {kw.cpc_pln ? `${kw.cpc_pln.toFixed(2)} zł` : '-'}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <OpportunityBar score={kw.opportunity_score || 0} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* History */}
      {!loading && !results && history.length > 0 && (
        <div style={{
          background: 'var(--bg-card)', borderRadius: 14, padding: 24, border: '1px solid var(--border)'
        }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            Historia analiz
          </h3>
          {history.map((h, i) => (
            <div key={i}
              style={{
                padding: '12px 0', borderBottom: i < history.length - 1 ? '1px solid var(--border)' : 'none',
                cursor: 'pointer'
              }}
              onClick={() => setResults(h.result)}
            >
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>
                {h.keywords?.join(', ') || 'Domyślne frazy podatkowe'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {new Date(h.created_at).toLocaleString('pl-PL')} - {h.result?.keywords?.length || 0} fraz
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
