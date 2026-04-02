import React, { useState, useEffect } from 'react';
import { Eye, Loader2, Plus, Trash2, RefreshCw, TrendingUp, AlertTriangle, Target, Globe, ChevronDown, ChevronUp, ArrowRight, Lightbulb } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;

const difficultyColor = (d) => d >= 70 ? '#ef4444' : d >= 40 ? '#f59e0b' : '#22c55e';
const scoreColor = (s) => s >= 80 ? '#22c55e' : s >= 60 ? '#f59e0b' : s >= 40 ? '#f97316' : '#ef4444';

export default function CompetitionMonitorPage() {
  const navigate = useNavigate();
  const [monitors, setMonitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [adding, setAdding] = useState(false);
  const [refreshingId, setRefreshingId] = useState(null);
  const [expanded, setExpanded] = useState({});

  const fetchMonitors = async () => {
    try {
      const { data } = await axios.get(`${API}/api/competition/monitors`);
      setMonitors(data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchMonitors(); }, []);

  const addMonitor = async () => {
    if (!keyword.trim()) return;
    setAdding(true);
    try {
      await axios.post(`${API}/api/competition/monitor`, { keyword: keyword.trim() });
      toast.success(`Dodano monitoring: "${keyword}"`);
      setKeyword('');
      fetchMonitors();
    } catch (e) {
      toast.error('Błąd dodawania');
    }
    setAdding(false);
  };

  const deleteMonitor = async (id) => {
    try {
      await axios.delete(`${API}/api/competition/monitors/${id}`);
      setMonitors(monitors.filter(m => m.id !== id));
      toast.success('Usunięto monitoring');
    } catch (e) { toast.error('Błąd usuwania'); }
  };

  const refreshMonitor = async (id) => {
    setRefreshingId(id);
    try {
      const { data } = await axios.post(`${API}/api/competition/monitors/${id}/refresh`);
      setMonitors(monitors.map(m => m.id === id ? data : m));
      toast.success('Analiza zaktualizowana');
    } catch (e) { toast.error('Błąd odświeżania'); }
    setRefreshingId(null);
  };

  const toggle = (id) => setExpanded(p => ({ ...p, [id]: !p[id] }));

  return (
    <div data-testid="competition-monitor-page" style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>Monitoring Konkurencji</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14 }}>
        Śledź pozycje konkurencji w SERP i znajdź luki w treściach
      </p>

      {/* Add keyword */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 32 }}>
        <input
          data-testid="competition-keyword-input"
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && addMonitor()}
          placeholder="Wpisz frazę do monitorowania..."
          style={{
            flex: 1, padding: '10px 14px', borderRadius: 8, fontSize: 14,
            border: '1px solid var(--border, hsl(215,16%,85%))',
            background: 'var(--bg-card, #fff)', color: 'var(--text-primary)',
          }}
        />
        <Button data-testid="add-monitor-btn" onClick={addMonitor} disabled={adding || !keyword.trim()} className="gap-2">
          {adding ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
          Monitoruj
        </Button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Loader2 size={24} className="animate-spin" style={{ color: 'var(--accent)', margin: '0 auto' }} />
        </div>
      )}

      {!loading && monitors.length === 0 && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)' }}>
          <Eye size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <p style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Brak monitorowanych fraz</p>
          <p style={{ fontSize: 13 }}>Dodaj frazę kluczową aby śledzić konkurencję</p>
        </div>
      )}

      {/* Monitors */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {monitors.map(mon => {
          const a = mon.analysis || {};
          const isExpanded = expanded[mon.id];
          return (
            <div key={mon.id} data-testid="competition-monitor-card" style={{
              border: '1px solid var(--border, hsl(215,16%,90%))',
              borderRadius: 12, overflow: 'hidden',
              background: 'var(--bg-card, #fff)',
            }}>
              {/* Header */}
              <div
                onClick={() => toggle(mon.id)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '14px 16px', cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Target size={18} style={{ color: 'var(--accent, #3b82f6)' }} />
                  <div>
                    <span style={{ fontSize: 15, fontWeight: 700 }}>{mon.keyword}</span>
                    <div style={{ display: 'flex', gap: 12, marginTop: 2, fontSize: 12, color: 'var(--text-secondary)' }}>
                      {a.difficulty != null && (
                        <span>Trudność: <strong style={{ color: difficultyColor(a.difficulty) }}>{a.difficulty}</strong></span>
                      )}
                      {a.monthly_volume != null && (
                        <span>Wolumen: <strong>{a.monthly_volume?.toLocaleString()}</strong>/mies</span>
                      )}
                      <span>Sprawdzono: {new Date(mon.last_checked).toLocaleDateString('pl-PL')}</span>
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Button size="sm" variant="ghost" onClick={e => { e.stopPropagation(); refreshMonitor(mon.id); }}
                    disabled={refreshingId === mon.id} title="Odśwież">
                    {refreshingId === mon.id ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={e => { e.stopPropagation(); deleteMonitor(mon.id); }}
                    title="Usuń" style={{ color: '#ef4444' }}>
                    <Trash2 size={14} />
                  </Button>
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              {isExpanded && (
                <div style={{ borderTop: '1px solid var(--border, hsl(215,16%,92%))' }}>
                  {/* Top Results */}
                  {a.top_results?.length > 0 && (
                    <div style={{ padding: '12px 16px' }}>
                      <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>
                        <Globe size={14} style={{ display: 'inline', verticalAlign: -2, marginRight: 6 }} />
                        TOP wyniki ({a.top_results.length})
                      </h4>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                            <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600 }}>#</th>
                            <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600 }}>Tytuł</th>
                            <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600 }}>Domena</th>
                            <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600 }}>Ruch</th>
                            <th style={{ textAlign: 'right', padding: '6px 8px', fontWeight: 600 }}>Score</th>
                          </tr>
                        </thead>
                        <tbody>
                          {a.top_results.map((r, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid var(--border, hsl(215,16%,95%))' }}>
                              <td style={{ padding: '8px', fontWeight: 700, color: 'var(--text-secondary)' }}>{r.position}</td>
                              <td style={{ padding: '8px', fontWeight: 500 }}>
                                <a href={r.url} target="_blank" rel="noopener noreferrer"
                                  style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                                  {r.title?.substring(0, 60)}{r.title?.length > 60 ? '...' : ''}
                                </a>
                              </td>
                              <td style={{ padding: '8px', color: 'var(--text-secondary)' }}>{r.domain}</td>
                              <td style={{ padding: '8px', textAlign: 'right' }}>{r.estimated_traffic?.toLocaleString()}</td>
                              <td style={{ padding: '8px', textAlign: 'right' }}>
                                <span style={{ color: scoreColor(r.content_score), fontWeight: 600 }}>{r.content_score}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Content Gaps + Recommendations */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0, borderTop: '1px solid var(--border, hsl(215,16%,92%))' }}>
                    {a.content_gaps?.length > 0 && (
                      <div style={{ padding: '12px 16px', borderRight: '1px solid var(--border, hsl(215,16%,92%))' }}>
                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: '#f59e0b' }}>
                          <AlertTriangle size={14} style={{ display: 'inline', verticalAlign: -2, marginRight: 6 }} />
                          Luki w treściach
                        </h4>
                        {a.content_gaps.map((g, i) => (
                          <div key={i} style={{ fontSize: 12, padding: '4px 0', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            • {g}
                          </div>
                        ))}
                      </div>
                    )}
                    {a.recommended_actions?.length > 0 && (
                      <div style={{ padding: '12px 16px' }}>
                        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: '#22c55e' }}>
                          <Lightbulb size={14} style={{ display: 'inline', verticalAlign: -2, marginRight: 6 }} />
                          Rekomendacje
                        </h4>
                        {a.recommended_actions.map((r, i) => (
                          <div key={i} style={{ fontSize: 12, padding: '4px 0', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            • {r}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Action button */}
                  <div style={{
                    padding: '10px 16px', background: 'var(--bg-muted, hsl(215,16%,97%))',
                    borderTop: '1px solid var(--border, hsl(215,16%,92%))',
                    display: 'flex', justifyContent: 'flex-end',
                  }}>
                    <Button size="sm" variant="outline" className="gap-1"
                      onClick={() => navigate(`/generator?keyword=${encodeURIComponent(mon.keyword)}`)}>
                      <ArrowRight size={12} /> Napisz artykuł na tę frazę
                    </Button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
