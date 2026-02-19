import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Loader2, Wand2, FileText, ArrowRight, ChevronDown, ChevronUp, BookOpen, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TEMPLATE_LABELS = {
  standard: 'Standardowy',
  poradnik: 'Poradnik',
  case_study: 'Case study',
  porownanie: 'Porownanie',
  checklist: 'Checklista',
  pillar: 'Pillar page',
  nowelizacja: 'Nowelizacja',
  kalkulator: 'Kalkulator'
};

const SeriesGenerator = () => {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [primaryKeyword, setPrimaryKeyword] = useState('');
  const [numParts, setNumParts] = useState(4);
  const [sourceText, setSourceText] = useState('');
  const [generating, setGenerating] = useState(false);
  const [outline, setOutline] = useState(null);
  const [expandedPart, setExpandedPart] = useState(null);
  const [generatingPart, setGeneratingPart] = useState(null);
  const [existingSeries, setExistingSeries] = useState([]);

  useEffect(() => {
    const fetchSeries = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/series`);
        setExistingSeries(res.data);
      } catch (err) {
        console.warn('Error loading series:', err);
      }
    };
    fetchSeries();
  }, []);

  const handleGenerateOutline = async () => {
    if (!topic.trim() || !primaryKeyword.trim()) {
      toast.error('Podaj temat i slowo kluczowe');
      return;
    }
    setGenerating(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/series/generate`, {
        topic: topic.trim(),
        primary_keyword: primaryKeyword.trim(),
        num_parts: numParts,
        source_text: sourceText
      }, { timeout: 120000 });
      
      setOutline(res.data);
      toast.success('Outline serii wygenerowany!');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad generowania';
      toast.error(msg);
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateArticle = async (part) => {
    setGeneratingPart(part.part_number);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/generate`, {
        topic: part.title,
        primary_keyword: part.primary_keyword,
        secondary_keywords: part.secondary_keywords || [],
        target_length: part.estimated_length || 1500,
        tone: 'profesjonalny',
        template: part.suggested_template || 'standard'
      }, { timeout: 180000 });
      
      toast.success(`Artykul "${part.title}" wygenerowany!`);
      navigate(`/editor/${res.data.id}`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad generowania artykulu';
      toast.error(msg);
    } finally {
      setGeneratingPart(null);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Seria artykulow</h1>
      </div>

      {/* Generator form */}
      {!outline ? (
        <div className="generator-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <Layers size={24} style={{ color: '#04389E' }} />
            <div>
              <h2 style={{ fontSize: 20, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>Zaplanuj serie artykulow</h2>
              <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', margin: '2px 0 0' }}>AI zaplanuje klaster tematyczny z linkowanie wewnetrznym</p>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Temat serii</label>
            <Input
              placeholder="np. Kompletny przewodnik po rozliczeniach CIT dla malych firm"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              data-testid="series-topic-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Glowne slowo kluczowe</label>
            <Input
              placeholder="np. rozliczenie CIT"
              value={primaryKeyword}
              onChange={(e) => setPrimaryKeyword(e.target.value)}
              data-testid="series-keyword-input"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Liczba artykulow w serii</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {[3, 4, 5, 6].map(n => (
                <button
                  key={n}
                  onClick={() => setNumParts(n)}
                  data-testid={`series-parts-${n}`}
                  style={{
                    padding: '8px 20px',
                    borderRadius: 8,
                    border: numParts === n ? '2px solid #04389E' : '1px solid hsl(214, 18%, 88%)',
                    background: numParts === n ? 'hsl(220, 95%, 98%)' : 'white',
                    color: numParts === n ? '#04389E' : 'hsl(215, 16%, 45%)',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Zrodla / Kontekst (opcjonalnie)</label>
            <textarea
              placeholder="Wklej tekst zrodlowy, notatki, przepisy prawne lub URL-e ktore maja byc uwzglednione w tresci..."
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              data-testid="series-source-input"
              rows={4}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: 8,
                border: '1px solid hsl(214, 18%, 88%)',
                fontSize: 13,
                resize: 'vertical',
                fontFamily: 'inherit',
                lineHeight: 1.5
              }}
            />
            <div className="form-hint">Wklej przepisy prawne, notatki lub zrodla — AI uwzgledni je w artkulach</div>
          </div>

          <Button
            onClick={handleGenerateOutline}
            disabled={generating || !topic.trim() || !primaryKeyword.trim()}
            size="lg"
            className="gap-2 w-full"
            data-testid="series-generate-button"
          >
            {generating ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Planowanie serii...
              </>
            ) : (
              <>
                <Wand2 size={20} />
                Zaplanuj serie
              </>
            )}
          </Button>
        </div>
      ) : (
        /* Outline view */
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <h2 style={{ fontSize: 24, margin: 0, fontFamily: "'Instrument Serif', Georgia, serif" }}>{outline.series_title}</h2>
              <p style={{ fontSize: 14, color: 'hsl(215, 16%, 45%)', marginTop: 4 }}>{outline.series_description}</p>
            </div>
            <Button variant="outline" onClick={() => setOutline(null)} data-testid="series-back-button">
              Nowa seria
            </Button>
          </div>

          {outline.seo_strategy && (
            <div style={{
              padding: '14px 18px',
              borderRadius: 10,
              background: 'hsl(220, 95%, 97%)',
              border: '1px solid hsl(220, 60%, 88%)',
              marginBottom: 20,
              fontSize: 13,
              color: '#04389E',
              lineHeight: 1.5
            }}>
              <strong>Strategia SEO:</strong> {outline.seo_strategy}
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {(outline.parts || []).map((part, idx) => {
              const isExpanded = expandedPart === idx;
              const isGenerating = generatingPart === part.part_number;
              return (
                <div
                  key={idx}
                  style={{
                    background: 'white',
                    border: '1px solid hsl(214, 18%, 88%)',
                    borderRadius: 12,
                    overflow: 'hidden'
                  }}
                  data-testid="series-part-card"
                >
                  <div
                    onClick={() => setExpandedPart(isExpanded ? null : idx)}
                    style={{
                      padding: '16px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{
                      width: 32, height: 32, borderRadius: 8,
                      background: '#04389E', color: 'white',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontFamily: "'Instrument Serif', Georgia, serif",
                      fontSize: 16, flexShrink: 0
                    }}>
                      {part.part_number}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 15, fontWeight: 600, color: 'hsl(222, 47%, 11%)' }}>{part.title}</div>
                      <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
                        <Badge variant="outline" style={{ fontSize: 10 }}>{TEMPLATE_LABELS[part.suggested_template] || part.suggested_template}</Badge>
                        <span style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)' }}>{part.estimated_length} slow</span>
                      </div>
                    </div>
                    {isExpanded ? <ChevronUp size={16} style={{ color: 'hsl(215, 16%, 65%)' }} /> : <ChevronDown size={16} style={{ color: 'hsl(215, 16%, 65%)' }} />}
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '0 20px 16px', borderTop: '1px solid hsl(214, 18%, 93%)' }}>
                      <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', lineHeight: 1.5, margin: '12px 0' }}>{part.summary}</p>
                      
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'hsl(222, 47%, 11%)', marginBottom: 6 }}>Kluczowe punkty:</div>
                      <ul style={{ margin: '0 0 12px', paddingLeft: 18, fontSize: 13, color: 'hsl(215, 16%, 40%)', lineHeight: 1.6 }}>
                        {(part.key_points || []).map((point, i) => (
                          <li key={i}>{point}</li>
                        ))}
                      </ul>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                        <span style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)' }}>Slowa kluczowe:</span>
                        {(part.secondary_keywords || []).map((kw, i) => (
                          <span key={i} className="keyword-tag" style={{ fontSize: 11 }}>{kw}</span>
                        ))}
                      </div>

                      <Button
                        onClick={() => handleGenerateArticle(part)}
                        disabled={!!generatingPart}
                        size="sm"
                        className="gap-1"
                        data-testid="series-generate-part-button"
                      >
                        {isGenerating ? (
                          <>
                            <Loader2 size={14} className="animate-spin" />
                            Generowanie...
                          </>
                        ) : (
                          <>
                            <ArrowRight size={14} />
                            Wygeneruj ten artykul
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Existing series */}
      {existingSeries.length > 0 && !outline && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 18, fontFamily: "'Instrument Serif', Georgia, serif", marginBottom: 12 }}>Poprzednie serie</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {existingSeries.map((s, idx) => (
              <div
                key={idx}
                style={{
                  background: 'white',
                  border: '1px solid hsl(214, 18%, 88%)',
                  borderRadius: 10,
                  padding: '14px 18px',
                  cursor: 'pointer'
                }}
                onClick={() => setOutline(s)}
                data-testid="existing-series-card"
              >
                <div style={{ fontSize: 15, fontWeight: 600, color: 'hsl(222, 47%, 11%)' }}>{s.series_title}</div>
                <div style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)', marginTop: 2 }}>
                  {(s.parts || []).length} artykulow
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SeriesGenerator;
