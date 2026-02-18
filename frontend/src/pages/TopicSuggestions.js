import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Lightbulb, Loader2, TrendingUp, BarChart2, ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const CATEGORIES = [
  { value: 'ogólne', label: 'Ogólne' },
  { value: 'vat', label: 'VAT' },
  { value: 'pit', label: 'PIT' },
  { value: 'cit', label: 'CIT' },
  { value: 'zus', label: 'ZUS' },
  { value: 'kadry', label: 'Kadry i płace' },
  { value: 'księgowość', label: 'Księgowość' },
  { value: 'działalność', label: 'Działalność gospodarcza' },
];

const TopicSuggestions = () => {
  const navigate = useNavigate();
  const [category, setCategory] = useState('ogólne');
  const [context, setContext] = useState('');
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchTopics = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/topics/suggest`, {
        category: category,
        context: context || `aktualne tematy z kategorii ${category} w Polsce`
      });
      setTopics(response.data.topics || []);
    } catch (error) {
      toast.error('Błąd podczas pobierania sugestii');
    } finally {
      setLoading(false);
    }
  };

  const handleUseTopic = (topic) => {
    navigate('/generator', { 
      state: { 
        topic: topic.title, 
        primaryKeyword: topic.primary_keyword,
        secondaryKeywords: topic.secondary_keywords || []
      } 
    });
  };

  const getVolumeColor = (volume) => {
    switch(volume) {
      case 'wysoki': return 'high';
      case 'średni': return 'medium';
      default: return 'low';
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch(difficulty) {
      case 'łatwa': return 'high';
      case 'średnia': return 'medium';
      default: return 'low';
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Sugestie tematów</h1>
      </div>

      {/* Filters */}
      <div style={{ 
        background: 'white', 
        border: '1px solid hsl(214, 18%, 88%)', 
        borderRadius: 12, 
        padding: 24, 
        marginBottom: 24,
        display: 'flex',
        gap: 16,
        alignItems: 'flex-end',
        flexWrap: 'wrap'
      }}>
        <div style={{ flex: '0 0 200px' }}>
          <label className="form-label">Kategoria</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid hsl(214, 18%, 88%)',
              borderRadius: 8,
              fontSize: 14,
              background: 'white'
            }}
            data-testid="topics-category-select"
          >
            {CATEGORIES.map(c => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label className="form-label">Kontekst (opcjonalnie)</label>
          <Input
            placeholder="np. zmiany podatkowe 2025, nowe przepisy..."
            value={context}
            onChange={(e) => setContext(e.target.value)}
            data-testid="topics-search-input"
          />
        </div>
        <Button 
          onClick={fetchTopics}
          disabled={loading}
          className="gap-2"
          data-testid="topics-generate-button"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
          Generuj sugestie
        </Button>
      </div>

      {/* Topics */}
      {loading ? (
        <div className="topics-grid">
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="topic-card">
              <div className="skeleton-line" style={{ height: 20, width: '80%' }} />
              <div className="skeleton-line" style={{ height: 14, width: '50%' }} />
              <div className="skeleton-line" style={{ height: 40, width: '100%' }} />
              <div className="skeleton-line" style={{ height: 32, width: '40%' }} />
            </div>
          ))}
        </div>
      ) : topics.length > 0 ? (
        <div className="topics-grid">
          {topics.map((topic, idx) => (
            <div key={idx} className="topic-card" data-testid="topics-topic-card">
              <div className="topic-card-title">{topic.title}</div>
              <div className="topic-card-keyword">
                <Search size={12} style={{ display: 'inline', marginRight: 4 }} />
                {topic.primary_keyword}
              </div>
              <div className="topic-card-desc">{topic.description}</div>
              <div className="topic-card-meta">
                <span className={`seo-badge ${getVolumeColor(topic.search_volume)}`}>
                  <TrendingUp size={12} /> {topic.search_volume}
                </span>
                <span className={`seo-badge ${getDifficultyColor(topic.seo_difficulty)}`}>
                  <BarChart2 size={12} /> {topic.seo_difficulty}
                </span>
                {topic.category && (
                  <span className="seo-badge medium">{topic.category}</span>
                )}
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleUseTopic(topic)}
                className="gap-1 w-full"
                data-testid="topics-use-topic-button"
              >
                Użyj w generatorze <ArrowRight size={14} />
              </Button>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Lightbulb size={64} className="empty-state-icon" />
          <h3>Odkryj tematy artykułów</h3>
          <p>Wybierz kategorię i kliknij "Generuj sugestie" aby otrzymać propozycje tematów SEO z zakresu księgowości.</p>
        </div>
      )}
    </div>
  );
};

export default TopicSuggestions;
