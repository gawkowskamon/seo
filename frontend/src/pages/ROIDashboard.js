import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, FileText, BarChart3, Award, AlertTriangle, Globe, Calendar, ArrowRight, Loader2, Target, Languages, Zap, CheckCircle2, XCircle, X } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const LANG_FLAGS = { pl: 'PL', en: 'EN', de: 'DE', uk: 'UA' };
const LANG_LABELS = { pl: 'Polski', en: 'English', de: 'Deutsch', uk: 'Українська' };

const StatCard = ({ icon: Icon, label, value, hint, color = '#04389E', testid }) => (
  <div data-testid={testid} style={{
    background: 'white', borderRadius: 12, padding: 20,
    border: '1px solid hsl(214, 18%, 88%)',
    display: 'flex', flexDirection: 'column', gap: 8
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10,
        background: `${color}15`, color,
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        <Icon size={18} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 55%)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</span>
    </div>
    <div style={{ fontSize: 32, fontWeight: 700, color: 'hsl(215, 16%, 15%)', lineHeight: 1, fontFamily: "'Instrument Serif', Georgia, serif" }}>{value}</div>
    {hint && <div style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)' }}>{hint}</div>}
  </div>
);

const DistributionBar = ({ label, count, total, color }) => {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13 }}>
        <span style={{ color: 'hsl(215, 16%, 35%)' }}>{label}</span>
        <span style={{ color: 'hsl(215, 16%, 55%)' }}><strong style={{ color }}>{count}</strong> ({Math.round(pct)}%)</span>
      </div>
      <div style={{ height: 8, background: 'hsl(215, 16%, 94%)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', background: color, width: `${pct}%`, transition: 'width 0.5s ease', borderRadius: 4 }} />
      </div>
    </div>
  );
};

const ROIDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bulkJob, setBulkJob] = useState(null);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkStarting, setBulkStarting] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/stats/roi`);
      setData(res.data);
    } catch (err) {
      console.error('ROI stats error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  // Poll bulk job status
  useEffect(() => {
    if (!bulkJob?.bulk_job_id || bulkJob.status !== 'running') return;
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/surfer/bulk-optimize/status/${bulkJob.bulk_job_id}`);
        setBulkJob(res.data);
        if (res.data.status !== 'running') {
          clearInterval(interval);
          const done = res.data.completed || 0;
          const failed = res.data.failed || 0;
          toast.success(`Optymalizacja zakończona: ${done} gotowe, ${failed} błędów`);
          fetchStats(); // refresh stats
        }
      } catch {
        // continue polling
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [bulkJob, fetchStats]);

  const startBulkOptimize = async () => {
    setBulkStarting(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/surfer/bulk-optimize?threshold=60&max_iterations=1`);
      toast.success(`Rozpoczęto optymalizację ${res.data.total_articles} artykułów`);
      // Fetch full status immediately
      const status = await axios.get(`${BACKEND_URL}/api/surfer/bulk-optimize/status/${res.data.bulk_job_id}`);
      setBulkJob(status.data);
      setShowBulkModal(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Błąd uruchamiania bulk optymalizacji');
    } finally {
      setBulkStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
        <Loader2 size={32} className="animate-spin" style={{ color: '#04389E' }} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-container">
        <div className="page-header"><h1>ROI Dashboard</h1></div>
        <p style={{ color: 'hsl(215, 16%, 55%)' }}>Brak danych do wyświetlenia.</p>
      </div>
    );
  }

  const total = data.total_articles || 0;
  const publishRate = total > 0 ? Math.round(((data.status_counts?.published || 0) / total) * 100) : 0;
  const maxMonthCount = Math.max(1, ...(data.monthly_trend || []).map(t => t.count));
  const weakCount = (data.score_buckets?.poor || 0) + (data.score_buckets?.medium || 0);

  return (
    <div className="page-container" data-testid="roi-dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
        <div>
          <h1>ROI Dashboard</h1>
          <p style={{ color: 'hsl(215, 16%, 55%)', marginTop: 4, fontSize: 14 }}>
            Szczegółowe statystyki wydajności treści i jakości SEO
          </p>
        </div>
        {weakCount > 0 && (
          <Button
            onClick={() => setShowBulkModal(true)}
            disabled={bulkStarting || bulkJob?.status === 'running'}
            className="gap-2"
            data-testid="bulk-optimize-trigger"
            style={{
              background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
              color: 'white', fontWeight: 600, padding: '10px 16px',
              border: 'none', borderRadius: 10
            }}
          >
            <Zap size={16} />
            Optymalizuj słabe ({weakCount})
          </Button>
        )}
      </div>

      {/* Top stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard testid="roi-total-articles" icon={FileText} label="Wszystkie artykuły" value={data.total_articles} hint={`${data.status_counts?.published || 0} opublikowanych`} color="#04389E" />
        <StatCard testid="roi-avg-surfer" icon={TrendingUp} label="Średni wynik SurferSEO" value={`${data.avg_surfer_score}%`} hint="Cel: 80%+" color={data.avg_surfer_score >= 80 ? '#16a34a' : data.avg_surfer_score >= 60 ? '#f59e0b' : '#ef4444'} />
        <StatCard testid="roi-publish-rate" icon={Target} label="Współczynnik publikacji" value={`${publishRate}%`} hint={`${data.status_counts?.draft || 0} w szkicu`} color="#8b5cf6" />
        <StatCard testid="roi-total-words" icon={BarChart3} label="Szacowana liczba słów" value={(data.total_words_estimate || 0).toLocaleString('pl-PL')} hint="Suma treści" color="#f59e0b" />
      </div>

      {/* Score distribution + Status distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 20, marginBottom: 32 }}>
        <div style={{ background: 'white', borderRadius: 12, padding: 20, border: '1px solid hsl(214, 18%, 88%)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Award size={16} style={{ color: '#04389E' }} />
            Rozkład jakości SEO
          </h3>
          <DistributionBar label="Doskonały (80-100%)" count={data.score_buckets?.excellent || 0} total={total} color="#16a34a" />
          <DistributionBar label="Dobry (70-79%)" count={data.score_buckets?.good || 0} total={total} color="#3b82f6" />
          <DistributionBar label="Do poprawy (50-69%)" count={data.score_buckets?.medium || 0} total={total} color="#f59e0b" />
          <DistributionBar label="Słaby (0-49%)" count={data.score_buckets?.poor || 0} total={total} color="#ef4444" />
        </div>

        <div style={{ background: 'white', borderRadius: 12, padding: 20, border: '1px solid hsl(214, 18%, 88%)' }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Calendar size={16} style={{ color: '#04389E' }} />
            Status artykułów
          </h3>
          <DistributionBar label="Opublikowane" count={data.status_counts?.published || 0} total={total} color="#16a34a" />
          <DistributionBar label="Zaplanowane" count={data.status_counts?.scheduled || 0} total={total} color="#8b5cf6" />
          <DistributionBar label="Szkice" count={data.status_counts?.draft || 0} total={total} color="#64748b" />
        </div>
      </div>

      {/* Language distribution */}
      {Object.keys(data.language_distribution || {}).length > 1 && (
        <div style={{ background: 'white', borderRadius: 12, padding: 20, border: '1px solid hsl(214, 18%, 88%)', marginBottom: 32 }} data-testid="roi-languages">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Languages size={16} style={{ color: '#04389E' }} />
            Rozkład językowy
          </h3>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {Object.entries(data.language_distribution).map(([lang, count]) => (
              <div key={lang} style={{
                padding: '10px 16px', borderRadius: 10,
                background: 'hsl(220, 95%, 98%)', border: '1px solid hsl(220, 60%, 90%)',
                display: 'flex', alignItems: 'center', gap: 10
              }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: '#04389E', background: 'white', padding: '3px 8px', borderRadius: 6 }}>
                  {LANG_FLAGS[lang] || lang.toUpperCase()}
                </span>
                <span style={{ fontSize: 13, color: 'hsl(215, 16%, 25%)' }}>{LANG_LABELS[lang] || lang}</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#04389E' }}>{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Monthly trend */}
      {(data.monthly_trend || []).length > 0 && (
        <div style={{ background: 'white', borderRadius: 12, padding: 20, border: '1px solid hsl(214, 18%, 88%)', marginBottom: 32 }} data-testid="roi-trend">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={16} style={{ color: '#04389E' }} />
            Trend publikacji (ostatnie 6 mies.)
          </h3>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 180, paddingTop: 20 }}>
            {data.monthly_trend.map((t, i) => {
              const h = Math.max(8, (t.count / maxMonthCount) * 140);
              return (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#04389E' }}>{t.count}</span>
                  <div style={{
                    width: '100%', maxWidth: 50, height: h,
                    background: `linear-gradient(to top, #04389E, #3b82f6)`,
                    borderRadius: '6px 6px 0 0', position: 'relative'
                  }} title={`${t.count} artykułów, śr. SEO: ${t.avg_score}%`}>
                    {t.avg_score > 0 && (
                      <span style={{
                        position: 'absolute', top: -18, left: '50%', transform: 'translateX(-50%)',
                        fontSize: 10, color: t.avg_score >= 70 ? '#16a34a' : '#f59e0b', fontWeight: 600
                      }}>{t.avg_score}%</span>
                    )}
                  </div>
                  <span style={{ fontSize: 10, color: 'hsl(215, 16%, 55%)' }}>{t.month.split('-')[1]}/{t.month.split('-')[0].slice(2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top and bottom performers */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 20 }}>
        <div style={{ background: 'white', borderRadius: 12, padding: 20, border: '1px solid hsl(214, 18%, 88%)' }} data-testid="roi-top-performers">          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, color: '#16a34a' }}>
            <Award size={16} />
            Top 5 artykułów
          </h3>
          {(data.top_performers || []).length === 0 ? (
            <p style={{ color: 'hsl(215, 16%, 55%)', fontSize: 13 }}>Brak danych</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {data.top_performers.map((a, i) => (
                <Link key={a.id} to={`/editor/${a.id}`} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                  borderRadius: 8, background: 'hsl(142, 50%, 97%)',
                  border: '1px solid hsl(142, 40%, 85%)', textDecoration: 'none'
                }}>
                  <span style={{
                    width: 28, height: 28, borderRadius: '50%',
                    background: 'hsl(142, 60%, 40%)', color: 'white',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 13, fontWeight: 700, flexShrink: 0
                  }}>{i + 1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'hsl(215, 16%, 15%)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.title}</div>
                    <div style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)' }}>{a.primary_keyword}</div>
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 800, color: '#16a34a' }}>{a.surfer_score?.percentage || 0}%</span>
                  <ArrowRight size={14} style={{ color: 'hsl(215, 16%, 55%)' }} />
                </Link>
              ))}
            </div>
          )}
        </div>

        <div style={{ background: 'white', borderRadius: 12, padding: 20, border: '1px solid hsl(214, 18%, 88%)' }} data-testid="roi-bottom-performers">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, color: '#ef4444' }}>
            <AlertTriangle size={16} />
            Do poprawy (5)
          </h3>
          {(data.bottom_performers || []).length === 0 ? (
            <p style={{ color: 'hsl(215, 16%, 55%)', fontSize: 13 }}>Brak artykułów wymagających poprawy</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {data.bottom_performers.map((a) => (
                <Link key={a.id} to={`/editor/${a.id}`} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px',
                  borderRadius: 8, background: 'hsl(0, 70%, 98%)',
                  border: '1px solid hsl(0, 50%, 88%)', textDecoration: 'none'
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'hsl(215, 16%, 15%)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.title}</div>
                    <div style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)' }}>{a.primary_keyword}</div>
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 800, color: '#ef4444' }}>{a.surfer_score?.percentage || 0}%</span>
                  <ArrowRight size={14} style={{ color: 'hsl(215, 16%, 55%)' }} />
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bulk Optimization Modal */}
      {showBulkModal && (
        <div
          data-testid="bulk-optimize-modal"
          onClick={(e) => { if (e.target === e.currentTarget && bulkJob?.status !== 'running') setShowBulkModal(false); }}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20
          }}
        >
          <div style={{
            background: 'white', borderRadius: 14, padding: 28, maxWidth: 720, width: '100%',
            maxHeight: '85vh', overflowY: 'auto', boxShadow: '0 25px 50px rgba(0,0,0,0.25)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6, fontFamily: "'Instrument Serif', Georgia, serif" }}>
                  Optymalizacja słabych artykułów
                </h2>
                <p style={{ color: 'hsl(215, 16%, 55%)', fontSize: 13 }}>
                  AI zoptymalizuje wszystkie artykuły ze score {'< 60%'}. Jeden artykuł na raz, ~2-3 min na artykuł.
                </p>
              </div>
              {bulkJob?.status !== 'running' && (
                <button onClick={() => setShowBulkModal(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'hsl(215, 16%, 55%)' }}>
                  <X size={20} />
                </button>
              )}
            </div>

            {!bulkJob && (
              <div>
                <div style={{
                  background: 'hsl(38, 90%, 95%)', border: '1px solid hsl(38, 90%, 85%)',
                  borderRadius: 10, padding: 16, marginBottom: 20, fontSize: 13, color: 'hsl(38, 80%, 30%)'
                }}>
                  <strong>⚠️ Uwaga:</strong> Zostanie zoptymalizowanych <strong>{weakCount} artykułów</strong>. Każdy artykuł zapisze automatycznie wersję przed optymalizacją (możesz cofnąć w historii). Całkowity czas: ~{Math.ceil(weakCount * 2.5)} minut.
                </div>
                <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                  <Button variant="outline" onClick={() => setShowBulkModal(false)} data-testid="bulk-cancel-btn">Anuluj</Button>
                  <Button
                    onClick={startBulkOptimize}
                    disabled={bulkStarting}
                    className="gap-2"
                    data-testid="bulk-confirm-btn"
                    style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)', color: 'white' }}
                  >
                    {bulkStarting ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
                    Start optymalizacji
                  </Button>
                </div>
              </div>
            )}

            {bulkJob && (
              <div data-testid="bulk-optimize-progress">
                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20
                }}>
                  <div style={{ background: 'hsl(220, 95%, 97%)', padding: 12, borderRadius: 8, textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#04389E', fontWeight: 600 }}>WSZYSTKIE</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: '#04389E' }}>{bulkJob.total}</div>
                  </div>
                  <div style={{ background: 'hsl(142, 50%, 97%)', padding: 12, borderRadius: 8, textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#16a34a', fontWeight: 600 }}>GOTOWE</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: '#16a34a' }}>{bulkJob.completed}</div>
                  </div>
                  <div style={{ background: 'hsl(0, 70%, 98%)', padding: 12, borderRadius: 8, textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: '#ef4444', fontWeight: 600 }}>BŁĘDY</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: '#ef4444' }}>{bulkJob.failed}</div>
                  </div>
                  <div style={{ background: 'hsl(215, 16%, 97%)', padding: 12, borderRadius: 8, textAlign: 'center' }}>
                    <div style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)', fontWeight: 600 }}>POZOSTAŁO</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: 'hsl(215, 16%, 30%)' }}>
                      {bulkJob.total - bulkJob.completed - bulkJob.failed}
                    </div>
                  </div>
                </div>

                {bulkJob.status === 'running' && bulkJob.current_article && (
                  <div style={{
                    background: 'hsl(220, 95%, 97%)', borderRadius: 10, padding: 12, marginBottom: 16,
                    display: 'flex', alignItems: 'center', gap: 10
                  }}>
                    <Loader2 size={18} className="animate-spin" style={{ color: '#04389E' }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 11, color: '#04389E', fontWeight: 600 }}>AKTUALNIE OPTYMALIZUJE</div>
                      <div style={{ fontSize: 13, color: 'hsl(215, 16%, 20%)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {bulkJob.current_article.title}
                      </div>
                    </div>
                  </div>
                )}

                <div style={{ maxHeight: 340, overflowY: 'auto', border: '1px solid hsl(214, 18%, 90%)', borderRadius: 10 }}>
                  {(bulkJob.articles || []).map((a, i) => (
                    <div key={i} data-testid="bulk-article-row" style={{
                      display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                      borderBottom: i < bulkJob.articles.length - 1 ? '1px solid hsl(214, 18%, 94%)' : 'none',
                      background: a.status === 'optimizing' ? 'hsl(220, 95%, 98%)' : 'transparent'
                    }}>
                      <div style={{ width: 22, display: 'flex', justifyContent: 'center' }}>
                        {a.status === 'done' && <CheckCircle2 size={18} style={{ color: '#16a34a' }} />}
                        {a.status === 'failed' && <XCircle size={18} style={{ color: '#ef4444' }} />}
                        {a.status === 'optimizing' && <Loader2 size={16} className="animate-spin" style={{ color: '#04389E' }} />}
                        {a.status === 'pending' && <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'hsl(215, 16%, 80%)' }} />}
                        {a.status === 'skipped' && <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'hsl(0, 50%, 75%)' }} />}
                      </div>
                      <div style={{ flex: 1, minWidth: 0, fontSize: 13, color: 'hsl(215, 16%, 20%)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {a.title}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, flexShrink: 0 }}>
                        <span style={{ color: 'hsl(215, 16%, 55%)' }}>{a.score_before ?? '?'}%</span>
                        <ArrowRight size={12} style={{ color: 'hsl(215, 16%, 55%)' }} />
                        <span style={{
                          fontWeight: 700,
                          color: a.score_after == null ? 'hsl(215, 16%, 55%)' :
                                 a.score_after > (a.score_before ?? 0) ? '#16a34a' :
                                 a.score_after < (a.score_before ?? 0) ? '#ef4444' : 'hsl(215, 16%, 40%)'
                        }}>
                          {a.score_after == null ? '—' : `${a.score_after}%`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {bulkJob.status !== 'running' && (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 20, gap: 10 }}>
                    <Button onClick={() => { setShowBulkModal(false); setBulkJob(null); }} data-testid="bulk-close-btn">
                      Zamknij
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ROIDashboard;
