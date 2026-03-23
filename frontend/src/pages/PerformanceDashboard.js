import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Activity, Users, FileText, TrendingUp, Image, Mail, Globe, CreditCard, Loader2, RefreshCw, Award, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const KPICard = ({ icon: Icon, label, value, sub, color = 'var(--accent)' }) => (
  <div className="perf-kpi-card" data-testid={`kpi-${label.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="perf-kpi-icon" style={{ background: `${color}15`, color }}>
      <Icon size={20} />
    </div>
    <div className="perf-kpi-body">
      <span className="perf-kpi-label">{label}</span>
      <span className="perf-kpi-value">{value}</span>
      {sub && <span className="perf-kpi-sub">{sub}</span>}
    </div>
  </div>
);

const SEO_COLORS = ['#16a34a', '#f59e0b', '#ef4444', '#94a3b8'];

const PerformanceDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/performance/dashboard`);
      setData(res.data);
    } catch (err) {
      if (err.response?.status === 403) {
        toast.error('Dostęp tylko dla administratorów');
      } else {
        toast.error('Błąd ładowania danych');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) {
    return (
      <div className="page-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <Loader2 size={32} className="animate-spin" style={{ color: 'var(--accent)' }} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <AlertTriangle size={48} style={{ color: 'var(--text-secondary)' }} />
          <h3>Brak danych</h3>
          <p>Nie udało się załadować danych dashboardu.</p>
          <Button onClick={fetchData} data-testid="performance-retry-button">Spróbuj ponownie</Button>
        </div>
      </div>
    );
  }

  const seoDistribution = [
    { name: 'Wysoki (80+)', value: data.seo?.high || 0 },
    { name: 'Średni (50-79)', value: data.seo?.medium || 0 },
    { name: 'Niski (<50)', value: data.seo?.low || 0 },
    { name: 'Brak oceny', value: data.seo?.no_score || 0 },
  ].filter(d => d.value > 0);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Dashboard wydajności</h1>
        <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="performance-refresh-button">
          <RefreshCw size={16} /> Odśwież
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="perf-kpi-grid" data-testid="performance-kpi-grid">
        <KPICard icon={Users} label="Użytkownicy" value={data.users?.total || 0} sub={`DAU: ${data.users?.dau || 0} / MAU: ${data.users?.mau || 0}`} color="#04389E" />
        <KPICard icon={FileText} label="Artykuły" value={data.articles?.total || 0} sub={`Ten tydzień: +${data.articles?.this_week || 0}`} color="#16a34a" />
        <KPICard icon={TrendingUp} label="Średni SEO" value={`${data.seo?.average || 0}%`} sub={`Max: ${data.seo?.max || 0}% / Min: ${data.seo?.min || 0}%`} color="#f59e0b" />
        <KPICard icon={Image} label="Obrazy" value={data.content?.images || 0} color="#8b5cf6" />
        <KPICard icon={Globe} label="WordPress" value={data.content?.wp_published || 0} sub="Opublikowane" color="#ec4899" />
        <KPICard icon={Mail} label="Newslettery" value={data.content?.newsletters || 0} color="#06b6d4" />
        <KPICard icon={CreditCard} label="Subskrypcje" value={data.subscriptions?.active || 0} sub="Aktywne" color="#F28C28" />
        <KPICard icon={Activity} label="Artykuły/mies." value={data.articles?.this_month || 0} color="#10b981" />
      </div>

      {/* Charts Row */}
      <div className="perf-charts-row">
        {/* Articles per day chart */}
        <div className="perf-chart-card" data-testid="performance-articles-chart">
          <h3 className="perf-chart-title">Artykuły utworzone (ostatnie 14 dni)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.articles?.per_day || []} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }} />
              <Bar dataKey="count" fill="#04389E" radius={[4, 4, 0, 0]} name="Artykuły" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* SEO Distribution pie */}
        <div className="perf-chart-card" data-testid="performance-seo-chart">
          <h3 className="perf-chart-title">Rozkład SEO</h3>
          {seoDistribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={seoDistribution} cx="50%" cy="50%" outerRadius={90} innerRadius={50} dataKey="value" paddingAngle={2}>
                  {seoDistribution.map((entry, idx) => (
                    <Cell key={idx} fill={SEO_COLORS[idx % SEO_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 13 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              Brak danych SEO
            </div>
          )}
          <div className="perf-legend">
            {seoDistribution.map((item, idx) => (
              <div key={idx} className="perf-legend-item">
                <div className="perf-legend-dot" style={{ background: SEO_COLORS[idx % SEO_COLORS.length] }} />
                <span>{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Articles & Recent */}
      <div className="perf-charts-row">
        <div className="perf-chart-card" data-testid="performance-top-articles">
          <h3 className="perf-chart-title"><Award size={16} style={{ display: 'inline', marginRight: 6 }} />Top 5 artykułów (SEO)</h3>
          <div className="perf-table">
            {(data.top_articles || []).map((article, idx) => (
              <div key={idx} className="perf-table-row">
                <span className="perf-table-rank">#{idx + 1}</span>
                <div className="perf-table-info">
                  <span className="perf-table-title">{article.title || 'Bez tytułu'}</span>
                  <span className="perf-table-keyword">{article.primary_keyword || ''}</span>
                </div>
                <span className={`seo-badge ${(article.seo_score?.percentage || 0) >= 80 ? 'high' : (article.seo_score?.percentage || 0) >= 50 ? 'medium' : 'low'}`}>
                  {article.seo_score?.percentage || 0}%
                </span>
              </div>
            ))}
            {(!data.top_articles || data.top_articles.length === 0) && (
              <p style={{ color: 'var(--text-secondary)', padding: 16, textAlign: 'center', fontSize: 13 }}>Brak artykułów z oceną SEO</p>
            )}
          </div>
        </div>

        <div className="perf-chart-card" data-testid="performance-recent-articles">
          <h3 className="perf-chart-title"><FileText size={16} style={{ display: 'inline', marginRight: 6 }} />Ostatnie artykuły</h3>
          <div className="perf-table">
            {(data.recent_articles || []).map((article, idx) => (
              <div key={idx} className="perf-table-row">
                <div className="perf-table-info">
                  <span className="perf-table-title">{article.title || 'Bez tytułu'}</span>
                  <span className="perf-table-keyword">{article.created_at ? new Date(article.created_at).toLocaleDateString('pl-PL') : ''}</span>
                </div>
                {article.seo_score?.percentage !== undefined && (
                  <span className={`seo-badge ${article.seo_score.percentage >= 80 ? 'high' : article.seo_score.percentage >= 50 ? 'medium' : 'low'}`}>
                    {article.seo_score.percentage}%
                  </span>
                )}
              </div>
            ))}
            {(!data.recent_articles || data.recent_articles.length === 0) && (
              <p style={{ color: 'var(--text-secondary)', padding: 16, textAlign: 'center', fontSize: 13 }}>Brak artykułów</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceDashboard;
