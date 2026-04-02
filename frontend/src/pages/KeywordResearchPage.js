import React, { useState } from 'react';
import { Search, Loader2, TrendingUp, TrendingDown, Minus, BarChart3, Target, ArrowRight, Plus } from 'lucide-react';
import { Button } from '../components/ui/button';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;

const difficultyColor = (d) => d >= 70 ? '#ef4444' : d >= 40 ? '#f59e0b' : '#22c55e';
const trendIcon = (t) => t === 'rosnący' ? <TrendingUp size={14} style={{color:'#22c55e'}} /> : t === 'malejący' ? <TrendingDown size={14} style={{color:'#ef4444'}} /> : <Minus size={14} style={{color:'#94a3b8'}} />;

export default function KeywordResearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [clusterLoading, setClusterLoading] = useState(false);
  const navigate = useNavigate();

  const research = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/surfer/keyword-research`, { seed_keyword: query });
      setResults(data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const clusterKeywords = async () => {
    if (!results?.keywords) return;
    setClusterLoading(true);
    try {
      const kws = results.keywords.map(k => k.keyword);
      const { data } = await axios.post(`${API}/api/surfer/content-planner`, { keywords: kws });
      setClusters(data);
    } catch (e) { console.error(e); }
    setClusterLoading(false);
  };

  return (
    <div data-testid="keyword-research-page" style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>Keyword Research</h1>
      <p style={{ color: 'var(--text-secondary, hsl(215,16%,55%))', marginBottom: 24, fontSize: 14 }}>Znajdź najlepsze słowa kluczowe dla Twojej strategii SEO</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 32 }}>
        <input data-testid="keyword-input" value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && research()}
          placeholder="Wpisz słowo kluczowe..." style={{ flex: 1, padding: '10px 14px', border: '1px solid var(--border, hsl(215,16%,85%))', borderRadius: 8, fontSize: 14, background: 'var(--bg-card, #fff)', color: 'var(--text-primary, #111)' }} />
        <Button data-testid="keyword-search-btn" onClick={research} disabled={loading} className="gap-2">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          Szukaj
        </Button>
      </div>

      {results && (
        <>
          {/* Main keyword info */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
            {[
              { label: 'Wolumen', value: results.main_keyword?.monthly_volume?.toLocaleString(), icon: BarChart3 },
              { label: 'Trudność', value: `${results.main_keyword?.difficulty}/100`, icon: Target },
              { label: 'CPC', value: `${results.main_keyword?.cpc_pln} PLN`, icon: TrendingUp },
              { label: 'Intencja', value: results.main_keyword?.search_intent, icon: Search },
            ].map((item, i) => (
              <div key={i} style={{ padding: 16, borderRadius: 12, border: '1px solid var(--border, hsl(215,16%,90%))', background: 'var(--bg-card, #fff)' }}>
                <item.icon size={18} style={{ color: 'var(--text-secondary, hsl(215,16%,55%))', marginBottom: 6 }} />
                <div style={{ fontSize: 22, fontWeight: 700 }}>{item.value}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{item.label}</div>
              </div>
            ))}
          </div>

          {/* Keywords table */}
          <div style={{ border: '1px solid var(--border, hsl(215,16%,90%))', borderRadius: 12, overflow: 'hidden', marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: 'var(--bg-muted, hsl(215,16%,97%))' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700 }}>Powiązane słowa kluczowe ({results.keywords?.length || 0})</h3>
              <Button size="sm" variant="outline" onClick={clusterKeywords} disabled={clusterLoading} className="gap-1">
                {clusterLoading ? <Loader2 size={14} className="animate-spin" /> : <Target size={14} />}
                Klastruj
              </Button>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: 'var(--bg-muted, hsl(215,16%,97%))', borderBottom: '1px solid var(--border, hsl(215,16%,90%))' }}>
                  <th style={{ textAlign: 'left', padding: '8px 16px', fontWeight: 600 }}>Słowo kluczowe</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>Wolumen</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>Trudność</th>
                  <th style={{ textAlign: 'center', padding: '8px 12px' }}>Trend</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px' }}>CPC</th>
                  <th style={{ textAlign: 'center', padding: '8px 12px' }}>Akcje</th>
                </tr>
              </thead>
              <tbody>
                {results.keywords?.map((kw, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border, hsl(215,16%,95%))' }}>
                    <td style={{ padding: '10px 16px', fontWeight: 500 }}>{kw.keyword}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>{kw.monthly_volume?.toLocaleString()}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>
                      <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600, background: `${difficultyColor(kw.difficulty)}15`, color: difficultyColor(kw.difficulty) }}>
                        {kw.difficulty}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center', padding: '10px 12px' }}>{trendIcon(kw.trend)}</td>
                    <td style={{ textAlign: 'right', padding: '10px 12px' }}>{kw.cpc_pln} zł</td>
                    <td style={{ textAlign: 'center', padding: '10px 12px' }}>
                      <Button size="sm" variant="ghost" className="gap-1" style={{ fontSize: 12 }}
                        onClick={() => navigate(`/generator?keyword=${encodeURIComponent(kw.keyword)}`)}>
                        <Plus size={12} /> Artykuł
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Clusters */}
          {clusters && (
            <div style={{ border: '1px solid var(--border, hsl(215,16%,90%))', borderRadius: 12, overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', background: 'var(--bg-muted, hsl(215,16%,97%))' }}>
                <h3 style={{ fontSize: 15, fontWeight: 700 }}>Content Plan — Klastry tematyczne ({clusters.clusters?.length || 0})</h3>
              </div>
              {clusters.clusters?.map((cluster, i) => (
                <div key={i} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border, hsl(215,16%,95%))' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontWeight: 700, fontSize: 14 }}>{cluster.topic}</span>
                      <span style={{ fontSize: 12, color: 'hsl(215,16%,55%)', marginLeft: 8 }}>{cluster.article_type}</span>
                    </div>
                    <Button size="sm" variant="outline" className="gap-1" style={{ fontSize: 12 }}
                      onClick={() => navigate(`/generator?keyword=${encodeURIComponent(cluster.primary_keyword)}`)}>
                      <ArrowRight size={12} /> Utwórz artykuł
                    </Button>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {cluster.keywords?.map((kw, j) => (
                      <span key={j} style={{ padding: '2px 8px', borderRadius: 10, background: 'var(--bg-muted, hsl(215,16%,94%))' }}>{kw}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
