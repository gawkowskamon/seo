import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Loader2, TrendingUp, BarChart2, Target, Clock, Tag, FileText, Filter, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PRIORITY_COLORS = { wysoki: '#ef4444', średni: '#f59e0b', niski: '#94a3b8' };
const DIFFICULTY_COLORS = { łatwa: '#16a34a', średnia: '#f59e0b', trudna: '#ef4444' };
const TYPE_ICONS = {
  poradnik: FileText,
  analiza: BarChart2,
  'case study': Target,
  lista: Tag,
  aktualności: Zap,
};

const AIArticleSuggestions = () => {
  const navigate = useNavigate();
  const [focus, setFocus] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pollingId, setPollingId] = useState(null);

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/ai-suggestions/status/${jobId}`);
      if (res.data.status === 'completed') {
        setSuggestions(res.data.result?.suggestions || []);
        setLoading(false);
        toast.success('Sugestie wygenerowane!');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd generowania sugestii');
      } else {
        setTimeout(() => pollStatus(jobId), 2000);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const generateSuggestions = async () => {
    setLoading(true);
    setSuggestions([]);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/ai-suggestions`, {
        count: 8,
        focus: focus
      });
      if (res.data.job_id) {
        setPollingId(res.data.job_id);
        setTimeout(() => pollStatus(res.data.job_id), 2000);
      }
    } catch (err) {
      setLoading(false);
      toast.error('Błąd uruchamiania generowania');
    }
  };

  const handleUseSuggestion = (suggestion) => {
    navigate('/generator', {
      state: {
        topic: suggestion.title,
        primaryKeyword: suggestion.primary_keyword,
        secondaryKeywords: suggestion.secondary_keywords || []
      }
    });
  };

  const getPriorityLabel = (p) => {
    switch (p) { case 'wysoki': return 'Wysoki'; case 'średni': return 'Średni'; default: return 'Niski'; }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Sugestie artykułów AI</h1>
      </div>

      <div className="ai-suggest-toolbar" data-testid="ai-suggestions-toolbar">
        <div style={{ flex: 1, minWidth: 200 }}>
          <label className="form-label">Obszar tematyczny (opcjonalnie)</label>
          <Input
            placeholder="np. zmiany w VAT 2026, nowe ulgi podatkowe..."
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            data-testid="ai-suggestions-focus-input"
          />
        </div>
        <Button
          onClick={generateSuggestions}
          disabled={loading}
          className="gap-2"
          data-testid="ai-suggestions-generate-button"
          style={{ alignSelf: 'flex-end' }}
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
          {loading ? 'Analizuję...' : 'Generuj sugestie AI'}
        </Button>
      </div>

      {loading && (
        <div className="ai-suggest-loading">
          <Loader2 size={28} className="animate-spin" style={{ color: '#04389E' }} />
          <p>AI analizuje istniejące artykuły i szuka luk w treści...</p>
          <div className="ai-suggest-skeleton-grid">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="topic-card" style={{ opacity: 0.4 }}>
                <div className="skeleton-line" style={{ height: 20, width: '75%' }} />
                <div className="skeleton-line" style={{ height: 14, width: '50%' }} />
                <div className="skeleton-line" style={{ height: 40, width: '100%' }} />
                <div className="skeleton-line" style={{ height: 32, width: '40%' }} />
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && suggestions.length > 0 && (
        <div className="topics-grid" data-testid="ai-suggestions-grid">
          {suggestions.map((s, idx) => {
            const TypeIcon = TYPE_ICONS[s.content_type] || FileText;
            return (
              <div key={idx} className="topic-card ai-suggest-card" data-testid="ai-suggestion-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span className="ai-suggest-type">
                    <TypeIcon size={12} /> {s.content_type || 'artykuł'}
                  </span>
                  <span className="ai-suggest-priority" style={{ color: PRIORITY_COLORS[s.priority] || '#94a3b8' }}>
                    {getPriorityLabel(s.priority)}
                  </span>
                </div>

                <div className="topic-card-title">{s.title}</div>

                <div className="topic-card-keyword" style={{ marginBottom: 4 }}>
                  <Target size={12} style={{ display: 'inline', marginRight: 4 }} />
                  {s.primary_keyword}
                </div>

                <div className="topic-card-desc">{s.description}</div>

                {s.rationale && (
                  <div className="ai-suggest-rationale">
                    <Sparkles size={11} /> {s.rationale}
                  </div>
                )}

                <div className="topic-card-meta">
                  {s.estimated_traffic && (
                    <span className="seo-badge medium">
                      <TrendingUp size={12} /> {s.estimated_traffic}
                    </span>
                  )}
                  <span className="seo-badge" style={{
                    background: `${DIFFICULTY_COLORS[s.difficulty] || '#94a3b8'}15`,
                    color: DIFFICULTY_COLORS[s.difficulty] || '#94a3b8',
                    border: `1px solid ${DIFFICULTY_COLORS[s.difficulty] || '#94a3b8'}30`
                  }}>
                    <BarChart2 size={12} /> {s.difficulty || 'średnia'}
                  </span>
                  {s.seasonal && (
                    <span className="seo-badge" style={{ background: '#dbeafe', color: '#1d4ed8', border: '1px solid #bfdbfe' }}>
                      <Clock size={12} /> sezonowy
                    </span>
                  )}
                </div>

                {s.secondary_keywords?.length > 0 && (
                  <div className="ai-suggest-keywords">
                    {s.secondary_keywords.slice(0, 4).map((kw, i) => (
                      <span key={i} className="ai-suggest-kw-tag">{kw}</span>
                    ))}
                  </div>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleUseSuggestion(s)}
                  className="gap-1 w-full"
                  data-testid="ai-suggestion-use-button"
                  style={{ marginTop: 8 }}
                >
                  Napisz artykuł <ArrowRight size={14} />
                </Button>
              </div>
            );
          })}
        </div>
      )}

      {!loading && suggestions.length === 0 && (
        <div className="empty-state">
          <Sparkles size={56} className="empty-state-icon" />
          <h3>Inteligentne sugestie artykułów</h3>
          <p>AI przeanalizuje Twoje istniejące artykuły, zidentyfikuje luki w treści i zaproponuje nowe tematy z wysokim potencjałem SEO.</p>
        </div>
      )}
    </div>
  );
};

export default AIArticleSuggestions;
