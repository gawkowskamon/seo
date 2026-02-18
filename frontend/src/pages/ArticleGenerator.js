import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Wand2, X, Loader2, BookOpen, Search, FileCheck, PenLine, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TONES = [
  { value: 'profesjonalny', label: 'Profesjonalny' },
  { value: 'ekspercki', label: 'Ekspercki' },
  { value: 'przyst\u0119pny', label: 'Przyst\u0119pny' },
  { value: 'formalny', label: 'Formalny' },
];

const LENGTHS = [
  { value: 1000, label: '1000 s\u0142\u00f3w' },
  { value: 1500, label: '1500 s\u0142\u00f3w' },
  { value: 2000, label: '2000 s\u0142\u00f3w' },
  { value: 2500, label: '2500 s\u0142\u00f3w' },
  { value: 3000, label: '3000 s\u0142\u00f3w' },
];

const STAGES = [
  { key: 'analyze', label: 'Analiza tematu i s\u0142\u00f3w kluczowych', icon: Search },
  { key: 'outline', label: 'Tworzenie struktury artyku\u0142u', icon: BookOpen },
  { key: 'write', label: 'Pisanie tre\u015bci i FAQ', icon: PenLine },
  { key: 'seo', label: 'Optymalizacja SEO i korekty', icon: FileCheck },
  { key: 'done', label: 'Finalizacja i ocena', icon: CheckCircle2 },
];

const ArticleGenerator = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [topic, setTopic] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [secondaryKeywords, setSecondaryKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [tone, setTone] = useState('profesjonalny');
  const [targetLength, setTargetLength] = useState(1500);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);

  // Pre-fill from topic suggestions
  useEffect(() => {
    if (location.state) {
      if (location.state.topic) setTopic(location.state.topic);
      if (location.state.primaryKeyword) setPrimaryKeyword(location.state.primaryKeyword);
      if (location.state.secondaryKeywords) setSecondaryKeywords(location.state.secondaryKeywords);
    }
  }, [location.state]);

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (kw && !secondaryKeywords.includes(kw)) {
      setSecondaryKeywords([...secondaryKeywords, kw]);
      setKeywordInput('');
    }
  };

  const removeKeyword = (kw) => {
    setSecondaryKeywords(secondaryKeywords.filter(k => k !== kw));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addKeyword();
    }
  };

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error('Podaj temat artyku\u0142u');
      return;
    }
    if (!primaryKeyword.trim()) {
      toast.error('Podaj g\u0142\u00f3wne s\u0142owo kluczowe');
      return;
    }

    setIsGenerating(true);
    setCurrentStage(0);

    // Simulate stage progression
    const stageInterval = setInterval(() => {
      setCurrentStage(prev => {
        if (prev < 3) return prev + 1;
        return prev;
      });
    }, 4000);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/articles/generate`, {
        topic: topic.trim(),
        primary_keyword: primaryKeyword.trim(),
        secondary_keywords: secondaryKeywords,
        target_length: targetLength,
        tone: tone
      });

      clearInterval(stageInterval);
      setCurrentStage(4);

      setTimeout(() => {
        toast.success('Artyku\u0142 wygenerowany pomy\u015blnie!');
        navigate(`/editor/${response.data.id}`);
      }, 1000);
    } catch (error) {
      clearInterval(stageInterval);
      setIsGenerating(false);
      const msg = error.response?.data?.detail || 'B\u0142\u0105d podczas generowania artyku\u0142u';
      toast.error(msg);
    }
  };

  if (isGenerating) {
    return (
      <div className="generation-overlay" data-testid="generation-progress">
        <div className="generation-card">
          <Wand2 size={40} style={{ color: 'hsl(209, 88%, 36%)', marginBottom: 16 }} />
          <h2>Generowanie artyku\u0142u</h2>
          <p style={{ color: 'hsl(215, 16%, 45%)', marginBottom: 24 }}>To mo\u017ce potrwa\u0107 15-30 sekund...</p>
          
          <div className="generation-stages">
            {STAGES.map((stage, idx) => (
              <div 
                key={stage.key}
                className={`generation-stage ${idx === currentStage ? 'active' : ''} ${idx < currentStage ? 'done' : ''}`}
                data-testid={`generation-stage-${stage.key}`}
              >
                {idx < currentStage ? (
                  <CheckCircle2 size={18} style={{ color: 'hsl(158, 55%, 34%)' }} />
                ) : idx === currentStage ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <stage.icon size={18} />
                )}
                <span data-testid="generation-stage-label">{stage.label}</span>
              </div>
            ))}
          </div>
          
          <div style={{ background: 'hsl(210, 22%, 96%)', borderRadius: 8, padding: 16, marginTop: 16 }}>
            <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', margin: 0 }}>
              Wskaz\u00f3wka: Artyku\u0142y z FAQ i spisem tre\u015bci osi\u0105gaj\u0105 \u015brednio 30% wi\u0119cej ruchu organicznego.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Nowy artyku\u0142 SEO</h1>
      </div>

      <div className="generator-card">
        {/* Topic */}
        <div className="form-group">
          <label className="form-label">Temat artyku\u0142u</label>
          <Input
            placeholder="np. Jak rozlicza\u0107 VAT w jednoosobowej dzia\u0142alno\u015bci gospodarczej"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            data-testid="generator-topic-input"
          />
          <div className="form-hint">Opisz dok\u0142adnie temat, kt\u00f3ry chcesz poruszy\u0107 w artykule</div>
        </div>

        {/* Primary keyword */}
        <div className="form-group">
          <label className="form-label">G\u0142\u00f3wne s\u0142owo kluczowe</label>
          <Input
            placeholder="np. rozliczanie VAT"
            value={primaryKeyword}
            onChange={(e) => setPrimaryKeyword(e.target.value)}
            data-testid="generator-keywords-input"
          />
          <div className="form-hint">Fraza, na kt\u00f3r\u0105 artyku\u0142 ma si\u0119 pozycjonowa\u0107</div>
        </div>

        {/* Secondary keywords */}
        <div className="form-group">
          <label className="form-label">S\u0142owa kluczowe dodatkowe</label>
          <div className="keywords-input-wrapper">
            {secondaryKeywords.map(kw => (
              <span key={kw} className="keyword-tag">
                {kw}
                <button onClick={() => removeKeyword(kw)} type="button">
                  <X size={14} />
                </button>
              </span>
            ))}
            <input
              className="keywords-input"
              placeholder="Wpisz i naci\u015bnij Enter..."
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={handleKeyDown}
              data-testid="generator-secondary-keywords-input"
            />
          </div>
          <div className="form-hint">Naci\u015bnij Enter aby doda\u0107 s\u0142owo kluczowe</div>
        </div>

        {/* Tone & Length */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <div className="form-group">
            <label className="form-label">Ton artyku\u0142u</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid hsl(214, 18%, 88%)',
                borderRadius: 8,
                fontSize: 14,
                background: 'white',
                cursor: 'pointer'
              }}
              data-testid="generator-tone-select"
            >
              {TONES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">D\u0142ugo\u015b\u0107 artyku\u0142u</label>
            <select
              value={targetLength}
              onChange={(e) => setTargetLength(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid hsl(214, 18%, 88%)',
                borderRadius: 8,
                fontSize: 14,
                background: 'white',
                cursor: 'pointer'
              }}
              data-testid="generator-length-slider"
            >
              {LENGTHS.map(l => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Generate button */}
        <Button
          onClick={handleGenerate}
          size="lg"
          className="gap-2 w-full mt-4"
          disabled={!topic.trim() || !primaryKeyword.trim()}
          data-testid="generator-generate-article-button"
        >
          <Wand2 size={20} />
          Wygeneruj artyku\u0142
        </Button>
      </div>
    </div>
  );
};

export default ArticleGenerator;
