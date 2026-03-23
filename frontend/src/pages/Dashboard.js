import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, FileText, TrendingUp, AlertTriangle, ArrowRight, Trash2, CheckSquare, Square, Tag, FolderOpen, X } from 'lucide-react';
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
  const [selected, setSelected] = useState(new Set());
  const [bulkMode, setBulkMode] = useState(false);
  const [categoryInput, setCategoryInput] = useState('');
  const [showCategoryInput, setShowCategoryInput] = useState(false);
  const [categories, setCategories] = useState([]);
  const [filterCategory, setFilterCategory] = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [articlesRes, statsRes, catsRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/articles`),
        axios.get(`${BACKEND_URL}/api/stats`),
        axios.get(`${BACKEND_URL}/api/articles/categories-list`).catch(() => ({ data: [] }))
      ]);
      setArticles(articlesRes.data);
      setStats(statsRes.data);
      setCategories(catsRes.data || []);
    } catch (error) {
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

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selected.size === filteredArticles.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filteredArticles.map(a => a.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!window.confirm(`Usunąć ${selected.size} artykułów?`)) return;
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/bulk-delete`, { article_ids: [...selected] });
      toast.success(`Usunięto ${res.data.deleted} artykułów`);
      setSelected(new Set());
      setBulkMode(false);
      fetchData();
    } catch (err) {
      toast.error('Błąd usuwania zbiorczego');
    }
  };

  const handleBulkCategory = async () => {
    if (selected.size === 0 || !categoryInput.trim()) return;
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/bulk-category`, {
        article_ids: [...selected],
        category: categoryInput.trim()
      });
      toast.success(`Skategoryzowano ${res.data.modified} artykułów jako "${categoryInput}"`);
      setCategoryInput('');
      setShowCategoryInput(false);
      setSelected(new Set());
      fetchData();
    } catch (err) {
      toast.error('Błąd kategoryzacji');
    }
  };

  const filteredArticles = articles.filter(a => {
    const matchesSearch = a.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.primary_keyword?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = !filterCategory || a.category === filterCategory;
    return matchesSearch && matchesCat;
  });

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
    return new Date(dateStr).toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Pulpit</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            variant={bulkMode ? 'default' : 'outline'}
            onClick={() => { setBulkMode(!bulkMode); setSelected(new Set()); setShowCategoryInput(false); }}
            data-testid="dashboard-bulk-mode-button"
            className="gap-1"
          >
            <CheckSquare size={16} /> {bulkMode ? 'Zakończ' : 'Zaznaczanie'}
          </Button>
          <Button onClick={() => navigate('/generator')} data-testid="dashboard-new-article-button" className="gap-2">
            <Plus size={18} /> Nowy artykuł
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-label">Wygenerowane artykuły</div>
          <div className="stat-card-value" data-testid="stat-total-articles">{loading ? '...' : stats.total_articles}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Śr. wynik SEO</div>
          <div className="stat-card-value score" data-testid="stat-avg-seo">{loading ? '...' : `${stats.avg_seo_score}%`}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Do poprawy</div>
          <div className="stat-card-value" data-testid="stat-needs-improvement">{loading ? '...' : stats.needs_improvement}</div>
        </div>
      </div>

      {/* Search + Category filter */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', minWidth: 250, flex: 1, maxWidth: 400 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <Input placeholder="Szukaj artykułów..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} style={{ paddingLeft: 36 }} data-testid="dashboard-search-input" />
        </div>
        {categories.length > 0 && (
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <FolderOpen size={14} style={{ color: 'var(--text-muted)' }} />
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text-primary)', fontSize: 13 }}
              data-testid="dashboard-category-filter"
            >
              <option value="">Wszystkie kategorie</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        )}
      </div>

      {/* Bulk Actions Bar */}
      {bulkMode && selected.size > 0 && (
        <div className="bulk-actions-bar" data-testid="dashboard-bulk-actions">
          <span style={{ fontSize: 13, fontWeight: 600 }}>Zaznaczono: {selected.size}</span>
          <Button size="sm" variant="destructive" onClick={handleBulkDelete} className="gap-1" data-testid="dashboard-bulk-delete">
            <Trash2 size={14} /> Usuń zaznaczone
          </Button>
          {!showCategoryInput ? (
            <Button size="sm" variant="outline" onClick={() => setShowCategoryInput(true)} className="gap-1" data-testid="dashboard-bulk-category-btn">
              <Tag size={14} /> Kategoryzuj
            </Button>
          ) : (
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <Input
                value={categoryInput}
                onChange={(e) => setCategoryInput(e.target.value)}
                placeholder="Nazwa kategorii..."
                style={{ width: 180, height: 32, fontSize: 12 }}
                onKeyDown={(e) => e.key === 'Enter' && handleBulkCategory()}
                data-testid="dashboard-bulk-category-input"
              />
              <Button size="sm" onClick={handleBulkCategory} disabled={!categoryInput.trim()} data-testid="dashboard-bulk-category-apply">Zastosuj</Button>
              <button onClick={() => setShowCategoryInput(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}><X size={14} /></button>
            </div>
          )}
        </div>
      )}

      {/* Articles Table */}
      {loading ? (
        <div className="articles-table" style={{ padding: 24 }}>
          {[1,2,3].map(i => <div key={i} className="skeleton-line" style={{ height: 48, marginBottom: 8 }} />)}
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="empty-state">
          <FileText size={64} className="empty-state-icon" />
          <h3>Brak artykułów</h3>
          <p>Wygeneruj pierwszy artykuł SEO dla swojego bloga księgowego.</p>
          <Button onClick={() => navigate('/generator')} className="gap-2"><Plus size={18} /> Wygeneruj artykuł</Button>
        </div>
      ) : (
        <div className="articles-table" data-testid="dashboard-articles-table">
          <table>
            <thead>
              <tr>
                {bulkMode && <th style={{ width: 40 }}>
                  <button onClick={selectAll} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }} data-testid="dashboard-select-all">
                    {selected.size === filteredArticles.length ? <CheckSquare size={16} /> : <Square size={16} />}
                  </button>
                </th>}
                <th>Tytuł</th>
                <th>Słowo kluczowe</th>
                <th>Kategoria</th>
                <th>Wynik SEO</th>
                <th>Data</th>
                <th>Akcje</th>
              </tr>
            </thead>
            <tbody>
              {filteredArticles.map((article) => (
                <tr key={article.id} style={selected.has(article.id) ? { background: 'var(--accent-light)' } : {}}>
                  {bulkMode && <td>
                    <button onClick={() => toggleSelect(article.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)' }}>
                      {selected.has(article.id) ? <CheckSquare size={16} style={{ color: 'var(--accent)' }} /> : <Square size={16} />}
                    </button>
                  </td>}
                  <td>
                    <Link to={`/editor/${article.id}`} className="article-title-link">{article.title}</Link>
                  </td>
                  <td>
                    <span className="keyword-tag" style={{ display: 'inline-flex' }}>{article.primary_keyword}</span>
                  </td>
                  <td>
                    {article.category && <span className="keyword-tag" style={{ display: 'inline-flex', background: 'var(--bg-muted)', fontSize: 11 }}>{article.category}</span>}
                  </td>
                  <td>
                    <span className={`seo-badge ${getSEOBadgeClass(article.seo_score?.percentage || 0)}`}>
                      {article.seo_score?.percentage || 0}% {getSEOLabel(article.seo_score?.percentage || 0)}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, color: 'var(--text-muted)' }}>{formatDate(article.created_at)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <Link to={`/editor/${article.id}`}>
                        <Button variant="outline" size="sm" className="gap-1">Edytuj <ArrowRight size={14} /></Button>
                      </Link>
                      <button className="btn-icon" onClick={(e) => handleDelete(e, article.id)} data-testid={`delete-article-${article.id}`} title="Usuń">
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
