import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, AlertTriangle, Send, Share2, TrendingUp, Target, Calendar, RefreshCw, Loader2, ArrowRight, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const InsightCard = ({ icon: Icon, iconColor, iconBg, title, count, children, empty, testid }) => (
  <div data-testid={testid} style={{
    background: 'white', borderRadius: 12, padding: 16,
    border: '1px solid hsl(214, 18%, 90%)', display: 'flex', flexDirection: 'column', gap: 10,
    minHeight: 180
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        width: 34, height: 34, borderRadius: 10,
        background: iconBg, color: iconColor,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
      }}>
        <Icon size={17} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: 'hsl(215, 16%, 25%)' }}>{title}</div>
        {count !== undefined && count > 0 && (
          <div style={{ fontSize: 11, color: iconColor, fontWeight: 600 }}>{count} {count === 1 ? 'pozycja' : 'pozycji'}</div>
        )}
      </div>
    </div>
    {empty ? (
      <p style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)', margin: 0, paddingTop: 4 }}>{empty}</p>
    ) : children}
  </div>
);

const ArticleListItem = ({ id, title, keyword, score, scoreColor = '#ef4444', to }) => (
  <Link to={to || `/editor/${id}`} style={{
    display: 'flex', alignItems: 'center', gap: 8, padding: '7px 9px',
    borderRadius: 7, background: 'hsl(215, 16%, 98%)', textDecoration: 'none',
    border: '1px solid hsl(215, 16%, 94%)', transition: 'all 0.12s'
  }} onMouseEnter={(e) => e.currentTarget.style.background = 'hsl(220, 95%, 97%)'}
     onMouseLeave={(e) => e.currentTarget.style.background = 'hsl(215, 16%, 98%)'}>
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{
        fontSize: 12, fontWeight: 500, color: 'hsl(215, 16%, 20%)',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
      }}>{title}</div>
      {keyword && <div style={{ fontSize: 10, color: 'hsl(215, 16%, 55%)' }}>{keyword}</div>}
    </div>
    {score !== undefined && score !== null && (
      <span style={{ fontSize: 11, fontWeight: 700, color: scoreColor, flexShrink: 0 }}>{score}%</span>
    )}
    <ArrowRight size={12} style={{ color: 'hsl(215, 16%, 55%)', flexShrink: 0 }} />
  </Link>
);

const SmartSchedulingWidget = () => {
  const navigate = useNavigate();
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchInsights = useCallback(async (forceRefresh = false) => {
    if (forceRefresh) setRefreshing(true); else setLoading(true);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/smart-scheduling/insights${forceRefresh ? '?refresh=true' : ''}`);
      setInsights(res.data);
    } catch (err) {
      console.error('Smart insights error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchInsights(); }, [fetchInsights]);

  const handleRefresh = async () => {
    await fetchInsights(true);
    toast.success('Insights odświeżone');
  };

  if (loading) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, hsl(220, 95%, 98%), hsl(270, 80%, 98%))',
        borderRadius: 14, padding: 24, marginBottom: 24,
        border: '1px solid hsl(214, 18%, 90%)', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 180
      }}>
        <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
      </div>
    );
  }

  if (!insights) return null;

  const totalActionable = (insights.needs_optimization?.length || 0) +
    (insights.ready_to_publish?.length || 0) +
    (insights.social_promotion?.length || 0) +
    (insights.content_gaps?.length || 0) +
    (insights.trending_topics?.length || 0);

  const cacheAge = insights.cached_at ?
    Math.round((Date.now() - new Date(insights.cached_at).getTime()) / 60000) : 0;

  return (
    <div data-testid="smart-scheduling-widget" style={{
      background: 'linear-gradient(135deg, hsl(220, 95%, 98%), hsl(270, 80%, 98%))',
      borderRadius: 14, padding: 24, marginBottom: 24,
      border: '1px solid hsl(220, 60%, 88%)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 42, height: 42, borderRadius: 12,
            background: 'linear-gradient(135deg, #7c3aed, #04389E)',
            color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Sparkles size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif", color: 'hsl(215, 16%, 15%)' }}>
              Smart Scheduling — insights na ten tydzień
            </h2>
            <p style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)', margin: '2px 0 0' }}>
              {totalActionable} zaleceń AI • cache odświeżany co 6h
              {insights.cached && cacheAge > 0 && <span> • wygenerowano {cacheAge} min temu</span>}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing} className="gap-2" data-testid="smart-scheduling-refresh">
          {refreshing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Odśwież
        </Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 14 }}>

        {/* Needs optimization */}
        <InsightCard
          testid="insight-needs-optimization"
          icon={AlertTriangle}
          iconColor="#ef4444"
          iconBg="hsl(0, 70%, 95%)"
          title="Zoptymalizuj te artykuły"
          count={insights.needs_optimization?.length}
          empty={(insights.needs_optimization?.length || 0) === 0 ? '✅ Wszystkie artykuły mają score ≥ 60%' : null}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {(insights.needs_optimization || []).slice(0, 3).map(a => (
              <ArticleListItem key={a.id} id={a.id} title={a.title} keyword={a.primary_keyword}
                score={a.surfer_score?.percentage} scoreColor="#ef4444" />
            ))}
            {(insights.needs_optimization?.length || 0) > 0 && (
              <Button variant="outline" size="sm" className="gap-1" onClick={() => navigate('/roi')} style={{ marginTop: 4, fontSize: 11 }}>
                Optymalizuj wszystkie <ArrowRight size={11} />
              </Button>
            )}
          </div>
        </InsightCard>

        {/* Ready to publish */}
        <InsightCard
          testid="insight-ready-to-publish"
          icon={Send}
          iconColor="#f59e0b"
          iconBg="hsl(38, 90%, 94%)"
          title="Gotowe do publikacji"
          count={insights.ready_to_publish?.length}
          empty={(insights.ready_to_publish?.length || 0) === 0 ? 'Brak szkiców ≥ 70% starszych niż 7 dni' : null}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {(insights.ready_to_publish || []).slice(0, 3).map(a => (
              <ArticleListItem key={a.id} id={a.id} title={a.title} keyword={a.primary_keyword}
                score={a.surfer_score?.percentage} scoreColor="#f59e0b" />
            ))}
          </div>
        </InsightCard>

        {/* Social promotion */}
        <InsightCard
          testid="insight-social-promotion"
          icon={Share2}
          iconColor="#16a34a"
          iconBg="hsl(142, 50%, 94%)"
          title="Promuj na social media"
          count={insights.social_promotion?.length}
          empty={(insights.social_promotion?.length || 0) === 0 ? 'Opublikuj artykuł w WordPress (z webhookiem) aby zobaczyć top kandydatów' : null}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {(insights.social_promotion || []).slice(0, 2).map(a => (
              <ArticleListItem key={a.id} id={a.id} title={a.title}
                keyword={`${a.wp_views_7d || 0} wyśw. (7d)`}
                score={a.surfer_score?.percentage} scoreColor="#16a34a"
                to={`/editor/${a.id}`} />
            ))}
          </div>
        </InsightCard>

        {/* Content gaps */}
        <InsightCard
          testid="insight-content-gaps"
          icon={Target}
          iconColor="#8b5cf6"
          iconBg="hsl(270, 80%, 94%)"
          title="Luki — brak pillar page"
          count={insights.content_gaps?.length}
          empty={(insights.content_gaps?.length || 0) === 0 ? 'Dobre pokrycie pillar pages w portfolio' : null}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {(insights.content_gaps || []).slice(0, 3).map((g, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 8, padding: '7px 9px',
                borderRadius: 7, background: 'hsl(215, 16%, 98%)', border: '1px solid hsl(215, 16%, 94%)'
              }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: 'hsl(215, 16%, 20%)' }}>{g.keyword}</div>
                  <div style={{ fontSize: 10, color: 'hsl(215, 16%, 55%)' }}>{g.article_count} artykułów, max {g.max_length} słów</div>
                </div>
              </div>
            ))}
          </div>
        </InsightCard>

        {/* Trending topics AI */}
        <InsightCard
          testid="insight-trending-topics"
          icon={TrendingUp}
          iconColor="#04389E"
          iconBg="hsl(220, 95%, 94%)"
          title="AI — trending tematy"
          count={insights.trending_topics?.length}
          empty={(insights.trending_topics?.length || 0) === 0 ? 'Potrzeba min. 3 artykułów do analizy historii' : null}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {(insights.trending_topics || []).slice(0, 2).map((t, i) => (
              <div key={i} style={{
                padding: '9px 10px', borderRadius: 8,
                background: 'hsl(220, 95%, 97%)', border: '1px solid hsl(220, 60%, 90%)'
              }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#04389E', marginBottom: 3 }}>{t.topic}</div>
                <div style={{ fontSize: 11, color: 'hsl(215, 16%, 45%)', marginBottom: 6, lineHeight: 1.4 }}>{t.reason}</div>
                <Button
                  size="sm"
                  className="gap-1"
                  data-testid={`trending-use-btn-${i}`}
                  onClick={() => navigate(`/generator?topic=${encodeURIComponent(t.topic || '')}&keyword=${encodeURIComponent(t.primary_keyword || '')}`)}
                  style={{ fontSize: 11, height: 26, padding: '0 10px', background: '#04389E' }}
                >
                  Użyj <ArrowRight size={11} />
                </Button>
              </div>
            ))}
          </div>
        </InsightCard>

        {/* Best publishing day */}
        <InsightCard
          testid="insight-best-day"
          icon={Calendar}
          iconColor="#059669"
          iconBg="hsl(160, 60%, 93%)"
          title="Najlepszy dzień publikacji"
        >
          <div style={{ textAlign: 'center', padding: '8px 0' }}>
            <div style={{
              fontSize: 28, fontWeight: 700, color: '#059669',
              fontFamily: "'Instrument Serif', Georgia, serif", textTransform: 'capitalize', lineHeight: 1
            }}>
              {insights.best_publishing_time?.day || 'wtorek'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, marginTop: 6, color: 'hsl(215, 16%, 45%)' }}>
              <Clock size={12} />
              <span style={{ fontSize: 12 }}>{insights.best_publishing_time?.hour_range || '9:00-11:00'}</span>
            </div>
            <div style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)', marginTop: 8, lineHeight: 1.4 }}>
              {insights.best_publishing_time?.reason}
            </div>
          </div>
        </InsightCard>

      </div>
    </div>
  );
};

export default SmartSchedulingWidget;
