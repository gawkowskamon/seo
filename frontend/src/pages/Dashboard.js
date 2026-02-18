import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, FileText, TrendingUp, AlertTriangle, ArrowRight, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Dashboard = () => {
  const navigate = useNavigate();
  const [articles, setArticles] = useState([]);
  const [stats, setStats] = useState({ total_articles: 0, avg_seo_score: 0, needs_improvement: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [articlesRes, statsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/articles`),
        axios.get(`${BACKEND_URL}/api/stats`)
      ]);
      setArticles(articlesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Błąd podczas ładowania danych');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, articleId) => {
    e.stopPropagation();
    e.preventDefault();
    if (!window.confirm('Czy na pewno chcesz usunąć ten artykuł?')) return;
    try {
      await axios.delete(`${BACKEND_URL}/api/articles/${articleId}`);
      toast.success('Artykuł usunięty');
      fetchData();
    } catch (error) {
      toast.error('Błąd podczas usuwania');
    }
  };

  const filteredArticles = articles.filter(a => 
    a.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.primary_keyword?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getSEOBadgeClass = (score) => {
    if (score >= 80) return 'high';
    if (score >= 50) return 'medium';
    return 'low';
  };

  const getSEOLabel = (score) => {
    if (score >= 80) return 'Dobry';
    if (score >= 50) return 'OK';
    return 'Słaby';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Pulpit</h1>
        <Button 
          onClick={() => navigate('/generator')}
          data-testid="dashboard-new-article-button"
          className="gap-2"
        >
          <Plus size={18} />
          Nowy artykuł
        </Button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-label">Wygenerowane artykuły</div>
          <div className="stat-card-value" data-testid="stat-total-articles">
            {loading ? '...' : stats.total_articles}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Śr. wynik SEO</div>
          <div className="stat-card-value score" data-testid="stat-avg-seo">
            {loading ? '...' : `${stats.avg_seo_score}%`}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Do poprawy</div>
          <div className="stat-card-value" data-testid="stat-needs-improvement">
            {loading ? '...' : stats.needs_improvement}
          </div>
        </div>
      </div>

      {/* Search */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ position: 'relative', maxWidth: 400 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 45%)' }} />
          <Input
            placeholder="Szukaj artykułów..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: 36 }}
            data-testid="dashboard-search-input"
          />
        </div>
      </div>

      {/* Articles Table */}
      {loading ? (
        <div className="articles-table" style={{ padding: 24 }}>
          {[1,2,3].map(i => (
            <div key={i} className="skeleton-line" style={{ height: 48, marginBottom: 8 }} />
          ))}
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="empty-state">
          <FileText size={64} className="empty-state-icon" />
          <h3>Brak artykułów</h3>
          <p>Wygeneruj pierwszy artykuł SEO dla swojego bloga księgowego.</p>
          <Button onClick={() => navigate('/generator')} className="gap-2">
            <Plus size={18} />
            Wygeneruj artykuł
          </Button>
        </div>
      ) : (
        <div className="articles-table" data-testid="dashboard-articles-table">
          <table>
            <thead>
              <tr>
                <th>Tytuł</th>
                <th>Słowo kluczowe</th>
                <th>Wynik SEO</th>
                <th>Data</th>
                <th>Akcje</th>
              </tr>
            </thead>
            <tbody>
              {filteredArticles.map((article) => (
                <tr key={article.id}>
                  <td>
                    <Link to={`/editor/${article.id}`} className="article-title-link">
                      {article.title}
                    </Link>
                  </td>
                  <td>
                    <span className="keyword-tag" style={{ display: 'inline-flex' }}>
                      {article.primary_keyword}
                    </span>
                  </td>
                  <td>
                    <span className={`seo-badge ${getSEOBadgeClass(article.seo_score?.percentage || 0)}`}>
                      {article.seo_score?.percentage || 0}% {getSEOLabel(article.seo_score?.percentage || 0)}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)' }}>
                    {formatDate(article.created_at)}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <Link to={`/editor/${article.id}`}>
                        <Button variant="outline" size="sm" className="gap-1">
                          Edytuj <ArrowRight size={14} />
                        </Button>
                      </Link>
                      <button 
                        className="btn-icon" 
                        onClick={(e) => handleDelete(e, article.id)}
                        data-testid={`delete-article-${article.id}`}
                        title="Usuń"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
