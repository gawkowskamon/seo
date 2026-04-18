import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Wand2, X, Loader2, BookOpen, Search, FileCheck, PenLine, CheckCircle2, FileText, ListOrdered, Briefcase, Columns, CheckSquare, Landmark, Scale, Calculator, Sparkles, TrendingUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TONES = [
  { value: 'profesjonalny', label: 'Profesjonalny' },
  { value: 'ekspercki', label: 'Ekspercki' },
  { value: 'przystepny', label: 'Przystepny' },
  { value: 'formalny', label: 'Formalny' },
];

const LENGTHS = [
  { value: '1000', label: '1000 slow' },
  { value: '1500', label: '1500 slow' },
  { value: '2000', label: '2000 slow' },
  { value: '2500', label: '2500 slow' },
  { value: '3000', label: '3000 slow' },
];

const LANGUAGES = [
  { value: 'pl', label: 'Polski', flag: 'PL' },
  { value: 'en', label: 'English', flag: 'EN' },
  { value: 'de', label: 'Deutsch', flag: 'DE' },
  { value: 'uk', label: 'Українська', flag: 'UA' },
];

const QUALITY_PRESETS = [
  {
    value: 'draft',
    label: 'Szybki draft',
    description: 'Bez auto-optymalizacji',
    time: '1-2 min',
    color: '#64748b',
    bg: 'hsl(215, 16%, 95%)'
  },
  {
    value: 'standard',
    label: 'Standard',
    description: '3 iteracje optymalizacji',
    time: '3-5 min',
    color: '#04389E',
    bg: 'hsl(220, 95%, 97%)'
  },
  {
    value: 'premium',
    label: 'Premium 80%+',
    description: 'Iteracje aż do celu (max 10)',
    time: '5-10 min',
    color: '#7c3aed',
    bg: 'hsl(270, 80%, 97%)'
  },
];

const STAGES = [
  { key: 'analyze', label: 'Analiza tematu i słów kluczowych', icon: Search },
  { key: 'outline', label: 'Tworzenie struktury artykułu', icon: BookOpen },
  { key: 'write', label: 'Pisanie treści i FAQ', icon: PenLine },
  { key: 'seo', label: 'Analiza SEO i SurferSEO SERP', icon: FileCheck },
  { key: 'optimize', label: 'Auto-optymalizacja do 80%+ (iteracyjnie)', icon: Sparkles },
  { key: 'done', label: 'Finalizacja artykułu', icon: CheckCircle2 },
];

const TEMPLATE_ICONS = {
  'file-text': FileText,
  'list-ordered': ListOrdered,
  'briefcase': Briefcase,
  'columns': Columns,
  'check-square': CheckSquare,
  'landmark': Landmark,
  'scale': Scale,
  'calculator': Calculator,
};

const CATEGORY_LABELS = {
  'podstawowe': 'Podstawowe',
  'specjalistyczne': 'Specjalistyczne',
  'zaawansowane': 'Zaawansowane'
};

const ArticleGenerator = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [topic, setTopic] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [secondaryKeywords, setSecondaryKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [tone, setTone] = useState('profesjonalny');
  const [targetLength, setTargetLength] = useState('1500');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  const [optimizationIterations, setOptimizationIterations] = useState([]);
  const [initialScore, setInitialScore] = useState(null);
  const [currentScore, setCurrentScore] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('standard');
  const [language, setLanguage] = useState('pl');
  const [qualityPreset, setQualityPreset] = useState('premium');

  useEffect(() => {
    if (location.state) {
      if (location.state.topic) setTopic(location.state.topic);
      if (location.state.primaryKeyword) setPrimaryKeyword(location.state.primaryKeyword);
      if (location.state.secondaryKeywords) setSecondaryKeywords(location.state.secondaryKeywords);
    }
    // Also support URL query params for deep-linking (e.g. from SmartSchedulingWidget)
    const params = new URLSearchParams(location.search);
    if (params.get('topic')) setTopic(params.get('topic'));
    if (params.get('keyword')) setPrimaryKeyword(params.get('keyword'));
  }, [location.state, location.search]);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/templates`);
        setTemplates(res.data);
      } catch (err) {
        console.warn('Could not load templates:', err);
      }
    };
    fetchTemplates();
  }, []);

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
      toast.error('Podaj temat artykulu');
      return;
    }
    if (!primaryKeyword.trim()) {
      toast.error('Podaj glowne slowo kluczowe');
      return;
    }

    setIsGenerating(true);
    setCurrentStage(0);

    try {
      // Start async generation
      const startRes = await axios.post(`${BACKEND_URL}/api/articles/generate`, {
        topic: topic.trim(),
        primary_keyword: primaryKeyword.trim(),
        secondary_keywords: secondaryKeywords,
        target_length: parseInt(targetLength),
        tone: tone,
        template: selectedTemplate,
        language: language,
        quality_preset: qualityPreset
      }, { timeout: 30000 });

      const jobId = startRes.data.job_id;
      let pollCount = 0;
      const maxPolls = 300; // 300 * 3s = 15 min max (optimization can take 10+ min)
      let notFoundCount = 0;
      
      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          pollCount++;
          const statusRes = await axios.get(`${BACKEND_URL}/api/articles/generate/status/${jobId}`);
          const { status, stage, article_id, error, optimization_iterations, initial_score, final_score } = statusRes.data;
          notFoundCount = 0; // reset on success
          
          // Map backend stage to UI stage:
          // stage 0: queued → UI 0 (analyze)
          // stage 1: generating → UI 2 (writing)
          // stage 3: article saved, running SERP → UI 3 (seo)
          // stage 5: optimizing iteratively → UI 4 (optimize)
          // stage 4: completed → UI 5 (done)
          let uiStage = 0;
          if (stage >= 4) uiStage = 5;
          else if (stage === 5 || status === 'optimizing') uiStage = 4;
          else if (stage === 3) uiStage = 3;
          else if (stage >= 1) uiStage = 2;
          setCurrentStage(uiStage);
          
          // Update optimization iteration state
          if (optimization_iterations && optimization_iterations.length > 0) {
            setOptimizationIterations(optimization_iterations);
            const last = optimization_iterations[optimization_iterations.length - 1];
            setCurrentScore(last.score_after ?? last.score_before ?? null);
          }
          if (initial_score !== undefined && initial_score !== null) setInitialScore(initial_score);
          if (final_score !== undefined && final_score !== null) setCurrentScore(final_score);
          
          if (status === 'completed' && article_id) {
            clearInterval(pollInterval);
            setCurrentStage(5);
            setTimeout(() => {
              const score = final_score ?? 0;
              if (score >= 80) {
                toast.success(`Artykuł wygenerowany! SEO score: ${score}% (cel osiągnięty ✓)`);
              } else if (score > 0) {
                toast.info(`Artykuł gotowy. SEO score: ${score}% — cel 80% nieosiągnięty, spróbuj ręcznej optymalizacji w edytorze.`, { duration: 6000 });
              } else {
                toast.success('Artykuł wygenerowany pomyślnie!');
              }
              navigate(`/editor/${article_id}`);
            }, 800);
          } else if (status === 'failed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            toast.error(error || 'Blad generowania artykulu');
          } else if (pollCount >= maxPolls) {
            clearInterval(pollInterval);
            setIsGenerating(false);
            toast.error('Generowanie trwa zbyt dlugo. Sprobuj ponownie.');
          }
        } catch (pollErr) {
          if (pollErr.response?.status === 404) {
            notFoundCount++;
            if (notFoundCount >= 3) {
              clearInterval(pollInterval);
              setIsGenerating(false);
              toast.error('Utracono polaczenie z procesem generowania. Sprobuj ponownie.');
            }
          } else {
            console.warn('Poll error:', pollErr.message);
          }
        }
      }, 3000);

    } catch (error) {
      setIsGenerating(false);
      const msg = error.response?.data?.detail || 'Blad podczas generowania artykulu';
      toast.error(msg);
    }
  };

  // Group templates by category
  const templatesByCategory = {};
  templates.forEach(t => {
    const cat = t.category || 'inne';
    if (!templatesByCategory[cat]) templatesByCategory[cat] = [];
    templatesByCategory[cat].push(t);
  });

  if (isGenerating) {
    const selectedTmpl = templates.find(t => t.id === selectedTemplate);
    return (
      <div className="generation-overlay" data-testid="generation-progress">
        <div className="generation-card">
          <Wand2 size={40} style={{ color: '#04389E', marginBottom: 16 }} />
          <h2>Generowanie artykulu</h2>
          {selectedTmpl && selectedTmpl.id !== 'standard' && (
            <p style={{ color: '#F28C28', fontWeight: 500, fontSize: 14, marginBottom: 4 }}>
              Szablon: {selectedTmpl.name}
            </p>
          )}
          <p style={{ color: 'hsl(215, 16%, 45%)', marginBottom: 24 }}>
            {currentStage >= 4 ? 'Auto-optymalizacja do 80%+ — to może potrwać 2-5 minut...' : 'To może potrwać 1-2 minuty...'}
          </p>
          
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

          {/* Optimization iterations progress */}
          {optimizationIterations.length > 0 && (
            <div data-testid="generation-optimization-progress" style={{
              marginTop: 18, padding: 16,
              background: 'linear-gradient(135deg, hsl(220, 95%, 98%), hsl(270, 80%, 98%))',
              border: '1px solid hsl(220, 60%, 88%)', borderRadius: 10
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <TrendingUp size={16} style={{ color: '#04389E' }} />
                <span style={{ fontWeight: 700, fontSize: 13, color: '#04389E' }}>
                  Optymalizacja iteracyjna do 80%+
                </span>
                {currentScore !== null && (
                  <span style={{
                    marginLeft: 'auto', fontWeight: 800, fontSize: 16,
                    color: currentScore >= 80 ? '#16a34a' : currentScore >= 60 ? '#f59e0b' : '#ef4444'
                  }}>
                    {currentScore}%
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {optimizationIterations.map((it, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 8, fontSize: 12,
                    padding: '5px 10px', borderRadius: 6,
                    background: it.phase === 'target_reached' ? 'hsl(142, 50%, 95%)' :
                                it.phase === 'stagnation' ? 'hsl(0, 50%, 96%)' :
                                it.phase === 'done' ? 'hsl(215, 16%, 97%)' : 'transparent'
                  }}>
                    <span style={{ fontWeight: 600, color: 'hsl(215, 16%, 35%)', minWidth: 60 }}>Iter {it.iteration}:</span>
                    <span style={{ color: 'hsl(215, 16%, 55%)' }}>{it.score_before ?? '?'}%</span>
                    <span style={{ color: 'hsl(215, 16%, 55%)' }}>→</span>
                    <span style={{
                      fontWeight: 700,
                      color: it.score_after === null || it.score_after === undefined ? 'hsl(215, 16%, 55%)' :
                             it.score_after >= 80 ? '#16a34a' :
                             it.score_after > (it.score_before ?? 0) ? '#04389E' : '#ef4444'
                    }}>
                      {it.score_after === null || it.score_after === undefined ? (
                        it.phase === 'start' ? <Loader2 size={12} className="animate-spin" style={{ display: 'inline' }} /> : '—'
                      ) : `${it.score_after}%`}
                    </span>
                    {it.phase === 'target_reached' && <span style={{ color: '#16a34a', marginLeft: 'auto', fontSize: 11 }}>✓ CEL</span>}
                    {it.phase === 'stagnation' && <span style={{ color: '#ef4444', marginLeft: 'auto', fontSize: 11 }}>⚠ Stagnacja</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div style={{ background: 'hsl(35, 35%, 97%)', borderRadius: 8, padding: 16, marginTop: 16 }}>
            <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', margin: 0 }}>
              Wskazowka: Artykuly z FAQ i spisem tresci osiagaja srednio 30% wiecej ruchu organicznego.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Nowy artykul SEO</h1>
      </div>

      {/* Template Selection */}
      {templates.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <label className="form-label" style={{ marginBottom: 12, display: 'block' }}>Wybierz szablon tresci</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {Object.entries(templatesByCategory).map(([cat, tmpls]) => (
              <div key={cat}>
                <div style={{ 
                  fontSize: 11, fontWeight: 600, color: 'hsl(215, 16%, 50%)', 
                  textTransform: 'uppercase', letterSpacing: '0.08em',
                  marginBottom: 8, fontFamily: "'IBM Plex Sans', sans-serif"
                }}>
                  {CATEGORY_LABELS[cat] || cat}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
                  {tmpls.map(tmpl => {
                    const IconComp = TEMPLATE_ICONS[tmpl.icon] || FileText;
                    const isSelected = selectedTemplate === tmpl.id;
                    return (
                      <button
                        key={tmpl.id}
                        onClick={() => setSelectedTemplate(tmpl.id)}
                        data-testid={`template-${tmpl.id}`}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 12,
                          padding: '14px 16px',
                          borderRadius: 10,
                          border: isSelected ? '2px solid #04389E' : '1px solid hsl(214, 18%, 88%)',
                          background: isSelected ? 'hsl(220, 95%, 98%)' : 'white',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'border-color 0.15s, background-color 0.15s',
                          width: '100%'
                        }}
                      >
                        <div style={{
                          width: 36, height: 36, borderRadius: 8,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          background: isSelected ? '#04389E' : 'hsl(35, 35%, 96%)',
                          color: isSelected ? 'white' : 'hsl(215, 16%, 45%)',
                          flexShrink: 0
                        }}>
                          <IconComp size={18} />
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ 
                            fontSize: 14, fontWeight: 600,
                            color: isSelected ? '#04389E' : 'hsl(222, 47%, 11%)',
                            lineHeight: 1.3
                          }}>
                            {tmpl.name}
                          </div>
                          <div style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)', lineHeight: 1.4, marginTop: 2 }}>
                            {tmpl.description}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="generator-card">
        <div className="form-group">
          <label className="form-label">Temat artykulu</label>
          <Input
            placeholder="np. Jak rozliczac VAT w jednoosobowej dzialalnosci gospodarczej"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            data-testid="generator-topic-input"
          />
          <div className="form-hint">Opisz dokladnie temat, ktory chcesz poruszyc w artykule</div>
        </div>

        <div className="form-group">
          <label className="form-label">Glowne slowo kluczowe</label>
          <Input
            placeholder="np. rozliczanie VAT"
            value={primaryKeyword}
            onChange={(e) => setPrimaryKeyword(e.target.value)}
            data-testid="generator-keywords-input"
          />
          <div className="form-hint">Fraza, na ktora artykul ma sie pozycjonowac</div>
        </div>

        <div className="form-group">
          <label className="form-label">Slowa kluczowe dodatkowe</label>
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
              placeholder="Wpisz i nacisnij Enter..."
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={handleKeyDown}
              data-testid="generator-secondary-keywords-input"
            />
          </div>
          <div className="form-hint">Nacisnij Enter aby dodac slowo kluczowe</div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
          <div className="form-group">
            <label className="form-label">Jezyk artykulu</label>
            <Select value={language} onValueChange={setLanguage} data-testid="generator-language-select">
              <SelectTrigger>
                <SelectValue placeholder="Wybierz jezyk" />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map(l => (
                  <SelectItem key={l.value} value={l.value} data-testid={`language-${l.value}`}>
                    <span style={{ fontWeight: 700, marginRight: 8, fontSize: 11, color: '#04389E' }}>{l.flag}</span>
                    {l.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="form-group">
            <label className="form-label">Ton artykulu</label>
            <Select value={tone} onValueChange={setTone} data-testid="generator-tone-select">
              <SelectTrigger>
                <SelectValue placeholder="Wybierz ton" />
              </SelectTrigger>
              <SelectContent>
                {TONES.map(t => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="form-group">
            <label className="form-label">Dlugosc artykulu</label>
            <Select value={targetLength} onValueChange={setTargetLength} data-testid="generator-length-slider">
              <SelectTrigger>
                <SelectValue placeholder="Wybierz dlugosc" />
              </SelectTrigger>
              <SelectContent>
                {LENGTHS.map(l => (
                  <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Quality Preset Selector */}
        <div className="form-group" style={{ marginTop: 20 }}>
          <label className="form-label">Jakość generowania</label>
          <div data-testid="generator-quality-preset" style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10, marginTop: 6
          }}>
            {QUALITY_PRESETS.map(preset => {
              const selected = qualityPreset === preset.value;
              return (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => setQualityPreset(preset.value)}
                  data-testid={`quality-preset-${preset.value}`}
                  style={{
                    padding: 14, borderRadius: 10, textAlign: 'left', cursor: 'pointer',
                    background: selected ? preset.bg : 'white',
                    border: `2px solid ${selected ? preset.color : 'hsl(214, 18%, 88%)'}`,
                    transition: 'all 0.15s'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Sparkles size={16} style={{ color: preset.color }} />
                    <span style={{ fontWeight: 700, color: selected ? preset.color : 'hsl(215, 16%, 20%)' }}>{preset.label}</span>
                  </div>
                  <div style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)', marginBottom: 4 }}>{preset.description}</div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: preset.color }}>⏱ {preset.time}</div>
                </button>
              );
            })}
          </div>
        </div>

        <Button
          onClick={handleGenerate}
          size="lg"
          className="gap-2 w-full mt-4"
          disabled={!topic.trim() || !primaryKeyword.trim()}
          data-testid="generator-generate-article-button"
        >
          <Wand2 size={20} />
          Wygeneruj artykul
        </Button>
      </div>
    </div>
  );
};

export default ArticleGenerator;
