import React, { useState } from 'react';
import { Globe, Loader2, AlertTriangle, CheckCircle2, Info, ArrowUpRight, Shield, FileText, Image, Link2, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const severityConfig = {
  krytyczny: { color: '#ef4444', bg: '#ef444415', icon: AlertTriangle, label: 'Krytyczny' },
  wysoki: { color: '#f97316', bg: '#f9731615', icon: AlertTriangle, label: 'Wysoki' },
  'średni': { color: '#f59e0b', bg: '#f59e0b15', icon: Info, label: 'Średni' },
  niski: { color: '#3b82f6', bg: '#3b82f615', icon: Info, label: 'Niski' },
};

const categoryIcons = {
  title: FileText, meta: FileText, headings: FileText, content: FileText,
  images: Image, links: Link2, performance: Zap, technical: Shield,
};

export default function URLAuditPage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [expandedIssues, setExpandedIssues] = useState({});

  const runAudit = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/surfer/audit-url`, { url });
      setResult(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const toggleIssue = (i) => setExpandedIssues(p => ({ ...p, [i]: !p[i] }));

  const scoreColor = (s) => s >= 80 ? '#22c55e' : s >= 60 ? '#f59e0b' : s >= 40 ? '#f97316' : '#ef4444';

  const groupedIssues = result?.issues?.reduce((acc, issue) => {
    const sev = issue.severity || 'niski';
    if (!acc[sev]) acc[sev] = [];
    acc[sev].push(issue);
    return acc;
  }, {}) || {};

  const severityOrder = ['krytyczny', 'wysoki', 'średni', 'niski'];

  return (
    <div data-testid="url-audit-page" style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>Audyt URL</h1>
      <p style={{ color: 'var(--text-secondary, hsl(215,16%,55%))', marginBottom: 24, fontSize: 14 }}>
        Przeanalizuj dowolny URL pod kątem optymalizacji SEO
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 32 }}>
        <input
          data-testid="url-audit-input"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && runAudit()}
          placeholder="https://twoja-strona.pl/artykul"
          style={{
            flex: 1, padding: '10px 14px',
            border: '1px solid var(--border, hsl(215,16%,85%))',
            borderRadius: 8, fontSize: 14,
            background: 'var(--bg-card, #fff)',
            color: 'var(--text-primary, #111)',
          }}
        />
        <Button data-testid="url-audit-btn" onClick={runAudit} disabled={loading || !url.trim()} className="gap-2">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Globe size={16} />}
          Audytuj
        </Button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Loader2 size={32} className="animate-spin" style={{ color: 'var(--accent, #3b82f6)', margin: '0 auto 12px' }} />
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Analizuję stronę...</p>
        </div>
      )}

      {result && (
        <>
          {/* Overall Score */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 24, padding: 24,
            borderRadius: 16, border: '1px solid var(--border, hsl(215,16%,90%))',
            background: 'var(--bg-card, #fff)', marginBottom: 24
          }}>
            <div style={{
              width: 80, height: 80, borderRadius: '50%',
              border: `4px solid ${scoreColor(result.overall_score)}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0
            }}>
              <span style={{ fontSize: 28, fontWeight: 800, color: scoreColor(result.overall_score) }}>
                {result.overall_score}
              </span>
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{result.title || url}</h2>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8, lineHeight: 1.5 }}>
                {result.meta_description || 'Brak meta description'}
              </p>
              <a href={url} target="_blank" rel="noopener noreferrer"
                style={{ fontSize: 12, color: 'var(--accent, #3b82f6)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                {url} <ArrowUpRight size={12} />
              </a>
            </div>
          </div>

          {/* Content Analysis Stats */}
          {result.content_analysis && (
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: 12, marginBottom: 24
            }}>
              {[
                { label: 'Słowa', value: result.content_analysis.word_count },
                { label: 'H1', value: result.content_analysis.h1_count },
                { label: 'H2', value: result.content_analysis.h2_count },
                { label: 'H3', value: result.content_analysis.h3_count },
                { label: 'Obrazy', value: result.content_analysis.image_count },
                { label: 'Linki wew.', value: result.content_analysis.internal_links },
                { label: 'Linki zew.', value: result.content_analysis.external_links },
              ].map((stat, i) => (
                <div key={i} style={{
                  padding: '12px 14px', borderRadius: 10,
                  border: '1px solid var(--border, hsl(215,16%,90%))',
                  background: 'var(--bg-card, #fff)',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{stat.value}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{stat.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Issues by severity */}
          <div style={{
            border: '1px solid var(--border, hsl(215,16%,90%))',
            borderRadius: 12, overflow: 'hidden', marginBottom: 24
          }}>
            <div style={{
              padding: '12px 16px',
              background: 'var(--bg-muted, hsl(215,16%,97%))',
              borderBottom: '1px solid var(--border, hsl(215,16%,90%))'
            }}>
              <h3 style={{ fontSize: 15, fontWeight: 700 }}>
                Problemy SEO ({result.issues?.length || 0})
              </h3>
            </div>
            {severityOrder.map(sev => {
              const issues = groupedIssues[sev];
              if (!issues?.length) return null;
              const cfg = severityConfig[sev] || severityConfig.niski;
              return (
                <div key={sev}>
                  <div style={{
                    padding: '8px 16px', fontSize: 12, fontWeight: 700,
                    color: cfg.color, background: cfg.bg,
                    borderBottom: '1px solid var(--border, hsl(215,16%,92%))',
                    textTransform: 'uppercase', letterSpacing: '0.05em'
                  }}>
                    {cfg.label} ({issues.length})
                  </div>
                  {issues.map((issue, i) => {
                    const key = `${sev}-${i}`;
                    const CatIcon = categoryIcons[issue.category] || Info;
                    return (
                      <div key={key} style={{ borderBottom: '1px solid var(--border, hsl(215,16%,95%))' }}>
                        <div
                          onClick={() => toggleIssue(key)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: 10,
                            padding: '10px 16px', cursor: 'pointer',
                            transition: 'background 0.1s',
                          }}
                        >
                          <CatIcon size={15} style={{ color: cfg.color, flexShrink: 0 }} />
                          <span style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{issue.issue}</span>
                          {expandedIssues[key] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </div>
                        {expandedIssues[key] && (
                          <div style={{
                            padding: '0 16px 12px 41px', fontSize: 13,
                            color: 'var(--text-secondary)', lineHeight: 1.6
                          }}>
                            <div style={{ marginBottom: 4 }}>
                              <strong>Rekomendacja:</strong> {issue.recommendation}
                            </div>
                            {issue.impact && (
                              <div style={{ fontSize: 12 }}>
                                <strong>Wpływ:</strong> {issue.impact}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* Opportunities */}
          {result.opportunities?.length > 0 && (
            <div style={{
              border: '1px solid var(--border, hsl(215,16%,90%))',
              borderRadius: 12, overflow: 'hidden'
            }}>
              <div style={{
                padding: '12px 16px',
                background: 'var(--bg-muted, hsl(215,16%,97%))',
                borderBottom: '1px solid var(--border, hsl(215,16%,90%))'
              }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: '#22c55e' }}>
                  <CheckCircle2 size={16} style={{ display: 'inline', verticalAlign: -3, marginRight: 6 }} />
                  Szanse na poprawę ({result.opportunities.length})
                </h3>
              </div>
              {result.opportunities.map((opp, i) => (
                <div key={i} style={{
                  padding: '12px 16px',
                  borderBottom: i < result.opportunities.length - 1 ? '1px solid var(--border, hsl(215,16%,95%))' : 'none'
                }}>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{opp.title}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{opp.description}</div>
                  {opp.estimated_impact && (
                    <span style={{
                      display: 'inline-block', marginTop: 6, fontSize: 11, fontWeight: 600,
                      padding: '2px 8px', borderRadius: 10,
                      background: opp.estimated_impact === 'wysoki' ? '#22c55e15' : '#f59e0b15',
                      color: opp.estimated_impact === 'wysoki' ? '#22c55e' : '#f59e0b',
                    }}>
                      Wpływ: {opp.estimated_impact}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
