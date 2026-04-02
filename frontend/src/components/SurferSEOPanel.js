import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, CheckCircle2, XCircle, MinusCircle, BarChart3, 
  FileText, Heading2, Image, List, Bold, HelpCircle, Link2,
  Loader2, RefreshCw, TrendingUp, Target, ChevronDown, ChevronUp,
  Zap, Eye, Globe
} from 'lucide-react';
import { Button } from '../components/ui/button';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const ScoreRing = ({ percentage, size = 120 }) => {
  const radius = (size - 12) / 2;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (percentage / 100) * circ;
  const color = percentage >= 80 ? '#22c55e' : percentage >= 60 ? '#f59e0b' : percentage >= 40 ? '#f97316' : '#ef4444';
  const label = percentage >= 80 ? 'Doskonały' : percentage >= 60 ? 'Dobry' : percentage >= 40 ? 'Do poprawy' : 'Słaby';
  
  return (
    <div style={{ position: 'relative', width: size, height: size, margin: '0 auto' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="hsl(215,16%,90%)" strokeWidth="8" />
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontSize: size * 0.3, fontWeight: 800, color, lineHeight: 1 }}>{percentage}</span>
        <span style={{ fontSize: 11, color: 'hsl(215,16%,55%)', marginTop: 2 }}>{label}</span>
      </div>
    </div>
  );
};

const MetricBar = ({ metric }) => {
  const pct = Math.min((metric.score / metric.max) * 100, 100);
  const color = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
  const icons = { 'Liczba słów': FileText, 'Nagłówki': Heading2, 'Obrazy': Image, 'Listy': List, 'Pogrubienia': Bold, 'FAQ': HelpCircle, 'Akapity': FileText, 'Tytuł i Meta': Target };
  const Icon = icons[metric.label] || BarChart3;

  return (
    <div style={{ padding: '8px 0', borderBottom: '1px solid hsl(215,16%,92%)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Icon size={14} style={{ color: 'hsl(215,16%,55%)' }} />
          <span style={{ fontSize: 13, fontWeight: 500 }}>{metric.label}</span>
        </div>
        <span style={{ fontSize: 12, fontWeight: 600, color }}>{metric.score}/{metric.max}</span>
      </div>
      <div style={{ height: 4, borderRadius: 2, background: 'hsl(215,16%,92%)' }}>
        <div style={{ height: '100%', borderRadius: 2, background: color, width: `${pct}%`, transition: 'width 0.5s ease' }} />
      </div>
      {metric.benchmark && (
        <div style={{ fontSize: 11, color: 'hsl(215,16%,55%)', marginTop: 3 }}>
          {typeof metric.value === 'object' 
            ? Object.entries(metric.value).map(([k,v]) => `${k}: ${v}`).join(' | ')
            : `Wartość: ${metric.value}`}
          {metric.benchmark.recommended && ` • Zalecane: ${metric.benchmark.recommended}`}
          {metric.benchmark.avg && !metric.benchmark.recommended && ` • Średnia: ${metric.benchmark.avg}`}
        </div>
      )}
    </div>
  );
};

const NlpTermItem = ({ term }) => {
  const statusIcon = term.status === 'ok' ? <CheckCircle2 size={13} style={{ color: '#22c55e' }} /> 
    : term.status === 'partial' ? <MinusCircle size={13} style={{ color: '#f59e0b' }} /> 
    : <XCircle size={13} style={{ color: '#ef4444' }} />;
  const importanceColors = { wysoka: '#ef4444', 'średnia': '#f59e0b', niska: '#94a3b8' };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0', fontSize: 13 }}>
      {statusIcon}
      <span style={{ flex: 1, fontWeight: term.importance === 'wysoka' ? 600 : 400 }}>{term.term}</span>
      <span style={{ fontSize: 11, color: 'hsl(215,16%,55%)' }}>{term.count}/{term.recommended}</span>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: importanceColors[term.importance] || '#94a3b8' }} />
    </div>
  );
};

const SurferSEOPanel = ({ article, onScoreUpdate }) => {
  const [surferData, setSurferData] = useState(article?.surfer_data || null);
  const [surferScore, setSurferScore] = useState(article?.surfer_score || null);
  const [analyzing, setAnalyzing] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [expanded, setExpanded] = useState({ metrics: true, nlp: true, competitors: false, outline: false });
  const [nlpFilter, setNlpFilter] = useState('all');

  useEffect(() => {
    if (article?.surfer_data && !surferData) setSurferData(article.surfer_data);
    if (article?.surfer_score && !surferScore) setSurferScore(article.surfer_score);
  }, [article]);

  const analyzeSERP = useCallback(async () => {
    if (!article?.primary_keyword) return;
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const { data } = await axios.post(`${API}/api/surfer/analyze-serp/async`, 
        { keyword: article.primary_keyword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const jobId = data.job_id;
      const poll = setInterval(async () => {
        try {
          const { data: status } = await axios.get(`${API}/api/surfer/analyze-serp/status/${jobId}`,
            { headers: { Authorization: `Bearer ${token}` } });
          if (status.status === 'completed') {
            clearInterval(poll);
            setSurferData(status.result);
            setAnalyzing(false);
            // Auto-score after analysis
            scoreArticle(status.result);
          } else if (status.status === 'failed') {
            clearInterval(poll);
            setAnalyzing(false);
          }
        } catch { clearInterval(poll); setAnalyzing(false); }
      }, 3000);
    } catch { setAnalyzing(false); }
  }, [article]);

  const scoreArticle = useCallback(async (data) => {
    const sd = data || surferData;
    if (!sd || !article?.id) return;
    setScoring(true);
    try {
      const token = localStorage.getItem('token');
      const { data: score } = await axios.post(`${API}/api/surfer/score`,
        { article_id: article.id, surfer_data: sd },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSurferScore(score);
      if (onScoreUpdate) onScoreUpdate(score);
    } catch (e) { console.error('Score error:', e); }
    setScoring(false);
  }, [surferData, article]);

  const toggle = (key) => setExpanded(p => ({ ...p, [key]: !p[key] }));

  // No data yet — show start screen
  if (!surferData) {
    return (
      <div data-testid="surfer-panel" style={{ padding: 24, textAlign: 'center' }}>
        <div style={{ width: 56, height: 56, borderRadius: 16, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
          <TrendingUp size={28} style={{ color: '#fff' }} />
        </div>
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Analiza SurferSEO</h3>
        <p style={{ fontSize: 13, color: 'hsl(215,16%,55%)', marginBottom: 16, lineHeight: 1.5 }}>
          Przeanalizuj konkurencję w SERP i zoptymalizuj artykuł pod kątem top wyników Google.
        </p>
        <Button data-testid="surfer-analyze-btn" onClick={analyzeSERP} disabled={analyzing || !article?.primary_keyword} className="gap-2">
          {analyzing ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          {analyzing ? 'Analizuję SERP...' : 'Analizuj SERP'}
        </Button>
        {!article?.primary_keyword && (
          <p style={{ fontSize: 12, color: '#ef4444', marginTop: 8 }}>Wprowadź słowo kluczowe aby rozpocząć</p>
        )}
      </div>
    );
  }

  const nlpTerms = surferScore?.metrics?.nlp_terms?.terms || surferData?.nlp_terms || [];
  const filteredTerms = nlpFilter === 'all' ? nlpTerms 
    : nlpFilter === 'missing' ? nlpTerms.filter(t => !t.used)
    : nlpTerms.filter(t => t.importance === nlpFilter);

  return (
    <div data-testid="surfer-panel" style={{ height: '100%', overflowY: 'auto' }}>
      {/* Score Ring */}
      <div style={{ padding: '20px 16px', borderBottom: '2px solid hsl(215,16%,92%)', textAlign: 'center' }}>
        {surferScore ? (
          <>
            <ScoreRing percentage={surferScore.percentage} />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 12 }}>
              <Button size="sm" variant="outline" onClick={() => scoreArticle()} disabled={scoring} className="gap-1" data-testid="surfer-rescore-btn">
                {scoring ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                Odśwież
              </Button>
              <Button size="sm" variant="outline" onClick={analyzeSERP} disabled={analyzing} className="gap-1">
                {analyzing ? <Loader2 size={13} className="animate-spin" /> : <Search size={13} />}
                Re-analiza
              </Button>
            </div>
          </>
        ) : (
          <div>
            <p style={{ fontSize: 13, color: 'hsl(215,16%,55%)', marginBottom: 8 }}>Dane SERP gotowe</p>
            <Button size="sm" onClick={() => scoreArticle()} disabled={scoring} className="gap-1">
              {scoring ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
              Oblicz wynik
            </Button>
          </div>
        )}
      </div>

      {/* SERP Info */}
      <div style={{ padding: '10px 16px', background: 'hsl(215,16%,97%)', display: 'flex', gap: 16, fontSize: 12, color: 'hsl(215,16%,45%)' }}>
        <span><Target size={12} style={{ display: 'inline', verticalAlign: -2 }} /> {surferData.search_intent}</span>
        <span><TrendingUp size={12} style={{ display: 'inline', verticalAlign: -2 }} /> Trudność: {surferData.difficulty}/100</span>
        <span><Eye size={12} style={{ display: 'inline', verticalAlign: -2 }} /> {surferData.monthly_volume?.toLocaleString()} /mies</span>
      </div>

      {/* Metrics */}
      <div style={{ padding: '0 16px' }}>
        <div onClick={() => toggle('metrics')} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', cursor: 'pointer', borderBottom: '1px solid hsl(215,16%,92%)' }}>
          <span style={{ fontSize: 14, fontWeight: 700 }}>Metryki treści</span>
          {expanded.metrics ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
        {expanded.metrics && surferScore && (
          <div>
            {Object.entries(surferScore.metrics).filter(([k]) => k !== 'nlp_terms').map(([key, metric]) => (
              <MetricBar key={key} metric={metric} />
            ))}
          </div>
        )}
      </div>

      {/* NLP Terms */}
      <div style={{ padding: '0 16px' }}>
        <div onClick={() => toggle('nlp')} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', cursor: 'pointer', borderBottom: '1px solid hsl(215,16%,92%)' }}>
          <span style={{ fontSize: 14, fontWeight: 700 }}>
            Terminy NLP
            {surferScore?.metrics?.nlp_terms && (
              <span style={{ fontSize: 12, fontWeight: 400, color: 'hsl(215,16%,55%)', marginLeft: 8 }}>
                {surferScore.metrics.nlp_terms.value}
              </span>
            )}
          </span>
          {expanded.nlp ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
        {expanded.nlp && (
          <>
            <div style={{ display: 'flex', gap: 4, padding: '8px 0', flexWrap: 'wrap' }}>
              {['all', 'missing', 'wysoka', 'średnia', 'niska'].map(f => (
                <button key={f} onClick={() => setNlpFilter(f)} 
                  style={{ fontSize: 11, padding: '3px 8px', borderRadius: 12, border: '1px solid', 
                    borderColor: nlpFilter === f ? '#3b82f6' : 'hsl(215,16%,85%)',
                    background: nlpFilter === f ? '#3b82f6' : 'transparent',
                    color: nlpFilter === f ? '#fff' : 'hsl(215,16%,45%)', cursor: 'pointer' }}>
                  {f === 'all' ? 'Wszystkie' : f === 'missing' ? 'Brakujące' : f}
                </button>
              ))}
            </div>
            <div style={{ maxHeight: 300, overflowY: 'auto' }}>
              {filteredTerms.map((term, i) => <NlpTermItem key={i} term={term} />)}
              {filteredTerms.length === 0 && <p style={{ fontSize: 12, color: 'hsl(215,16%,55%)', padding: 8 }}>Brak terminów</p>}
            </div>
          </>
        )}
      </div>

      {/* Competitors */}
      <div style={{ padding: '0 16px' }}>
        <div onClick={() => toggle('competitors')} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', cursor: 'pointer', borderBottom: '1px solid hsl(215,16%,92%)' }}>
          <span style={{ fontSize: 14, fontWeight: 700 }}>Konkurencja TOP {surferData.top_competitors?.length || 0}</span>
          {expanded.competitors ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
        {expanded.competitors && surferData.top_competitors?.map((comp, i) => (
          <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid hsl(215,16%,95%)', fontSize: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 20, height: 20, borderRadius: '50%', background: 'hsl(215,16%,92%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700 }}>{comp.position}</span>
              <span style={{ flex: 1, fontWeight: 500, fontSize: 13 }}>{comp.title}</span>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 4, color: 'hsl(215,16%,55%)' }}>
              <span>{comp.word_count} słów</span>
              <span>{comp.h2_count} H2</span>
              <span>Score ~{comp.score_estimate}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Suggested Outline */}
      <div style={{ padding: '0 16px 16px' }}>
        <div onClick={() => toggle('outline')} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 0', cursor: 'pointer', borderBottom: '1px solid hsl(215,16%,92%)' }}>
          <span style={{ fontSize: 14, fontWeight: 700 }}>Sugerowana struktura</span>
          {expanded.outline ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
        {expanded.outline && surferData.content_outline_suggestion?.map((item, i) => (
          <div key={i} style={{ padding: '4px 0', fontSize: 13, paddingLeft: item.startsWith('H3') ? 16 : 0, color: item.startsWith('H2') ? 'hsl(215,16%,25%)' : 'hsl(215,16%,45%)', fontWeight: item.startsWith('H2') ? 600 : 400 }}>
            {item}
          </div>
        ))}
        {expanded.outline && surferData.questions_to_answer?.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <p style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215,16%,45%)', marginBottom: 4 }}>Pytania do uwzględnienia:</p>
            {surferData.questions_to_answer.map((q, i) => (
              <div key={i} style={{ padding: '3px 0', fontSize: 12, color: 'hsl(215,16%,55%)', display: 'flex', gap: 4 }}>
                <HelpCircle size={12} style={{ marginTop: 2, flexShrink: 0 }} /> {q}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SurferSEOPanel;
