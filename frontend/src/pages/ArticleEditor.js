import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, Eye, Code, BarChart3, Share2, ChevronLeft, Loader2, RefreshCw, Wand2, Cloud, CloudOff, Image as ImageIcon, Sparkles, Link2, CalendarClock, MessageSquare } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import SEOScorePanel from '../components/SEOScorePanel';
import ExportPanel from '../components/ExportPanel';
import FAQEditor from '../components/FAQEditor';
import TOCPanel from '../components/TOCPanel';
import ImageGenerator from '../components/ImageGenerator';
import SEOAssistantPanel from '../components/SEOAssistantPanel';
import EditorToolbar from '../components/EditorToolbar';
import AIChatPanel from '../components/AIChatPanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ArticleEditor = () => {
  const { articleId } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [regenerating, setRegenerating] = useState(null); // null, 'faq', 'meta'
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const autosaveTimerRef = useRef(null);
  const editorContentRef = useRef(null);
  
  const [editorTab, setEditorTab] = useState('visual');
  const [rightTab, setRightTab] = useState('seo');
  const [htmlContent, setHtmlContent] = useState('');
  
  const [metaTitle, setMetaTitle] = useState('');
  const [metaDescription, setMetaDescription] = useState('');

  useEffect(() => {
    fetchArticle();
    return () => {
      if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [articleId]);

  // Autosave with debounce
  useEffect(() => {
    if (!article || !hasUnsavedChanges) return;
    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    autosaveTimerRef.current = setTimeout(() => {
      performAutosave();
    }, 10000); // 10 second debounce
    return () => {
      if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metaTitle, metaDescription, article?.faq, hasUnsavedChanges]);

  const performAutosave = async () => {
    if (!article || saving) return;
    try {
      await saveArticle(true);
    } catch (e) {
      // Silent fail for autosave
    }
  };

  const fetchArticle = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/articles/${articleId}`);
      setArticle(response.data);
      setHtmlContent(buildHtmlFromArticle(response.data));
      setMetaTitle(response.data.meta_title || '');
      setMetaDescription(response.data.meta_description || '');
      setHasUnsavedChanges(false);
    } catch (error) {
      toast.error('Błąd podczas ładowania artykułu');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const buildHtmlFromArticle = (art) => {
    if (!art) return '';
    let html = `<h1>${art.title || ''}</h1>\n\n`;
    for (const section of (art.sections || [])) {
      html += `<h2 id="${section.anchor}">${section.heading}</h2>\n`;
      html += `${section.content || ''}\n\n`;
      for (const sub of (section.subsections || [])) {
        html += `<h3 id="${sub.anchor}">${sub.heading}</h3>\n`;
        html += `${sub.content || ''}\n\n`;
      }
    }
    if (art.faq && art.faq.length > 0) {
      html += `<h2>FAQ</h2>\n`;
      for (const faq of art.faq) {
        html += `<h3>${faq.question}</h3>\n`;
        html += `<p>${faq.answer}</p>\n\n`;
      }
    }
    return html;
  };

  const saveArticle = async (isAutosave = false) => {
    if (!article) return;
    setSaving(true);
    try {
      const updateData = {
        title: article.title,
        slug: article.slug,
        meta_title: metaTitle,
        meta_description: metaDescription,
        sections: article.sections,
        faq: article.faq,
        toc: article.toc,
        internal_link_suggestions: article.internal_link_suggestions,
        sources: article.sources,
        html_content: htmlContent
      };
      const response = await axios.put(`${BACKEND_URL}/api/articles/${articleId}`, updateData);
      setArticle(response.data);
      setHasUnsavedChanges(false);
      if (!isAutosave) {
        toast.success('Artykuł zapisany');
      }
    } catch (error) {
      if (!isAutosave) {
        toast.error('Błąd podczas zapisywania');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSave = () => saveArticle(false);

  const handleRescore = async () => {
    if (!article) return;
    setScoring(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/score`, {
        primary_keyword: article.primary_keyword || '',
        secondary_keywords: article.secondary_keywords || []
      });
      setArticle(prev => ({ ...prev, seo_score: response.data }));
      toast.success('Wynik SEO zaktualizowany');
    } catch (error) {
      toast.error('Błąd podczas obliczania wyniku');
    } finally {
      setScoring(false);
    }
  };

  const handleRegenerateFAQ = async () => {
    if (!article) return;
    setRegenerating('faq');
    try {
      const response = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/regenerate`, {
        section: 'faq'
      }, { timeout: 60000 });
      if (response.data.faq) {
        setArticle(prev => ({ ...prev, faq: response.data.faq }));
        setHasUnsavedChanges(true);
        toast.success('FAQ zregenerowane');
      }
    } catch (error) {
      toast.error('Błąd regeneracji FAQ');
    } finally {
      setRegenerating(null);
    }
  };

  const handleRegenerateMeta = async () => {
    if (!article) return;
    setRegenerating('meta');
    try {
      const response = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/regenerate`, {
        section: 'meta'
      }, { timeout: 60000 });
      if (response.data.meta_title) {
        setMetaTitle(response.data.meta_title);
        setMetaDescription(response.data.meta_description || '');
        setHasUnsavedChanges(true);
        toast.success('Meta dane zregenerowane');
      }
    } catch (error) {
      toast.error('Błąd regeneracji meta danych');
    } finally {
      setRegenerating(null);
    }
  };

  const updateFAQ = (newFaq) => {
    setArticle(prev => ({ ...prev, faq: newFaq }));
    setHasUnsavedChanges(true);
  };

  const handleMetaTitleChange = (e) => {
    setMetaTitle(e.target.value);
    setHasUnsavedChanges(true);
  };

  const handleMetaDescChange = (e) => {
    setMetaDescription(e.target.value);
    setHasUnsavedChanges(true);
  };

  const handleApplySuggestion = (suggestion) => {
    if (!suggestion.apply_target || suggestion.apply_target === 'none') return;
    
    switch (suggestion.apply_target) {
      case 'meta_title':
        if (suggestion.proposed_value) {
          setMetaTitle(suggestion.proposed_value);
          setHasUnsavedChanges(true);
        }
        break;
      case 'meta_description':
        if (suggestion.proposed_value) {
          setMetaDescription(suggestion.proposed_value);
          setHasUnsavedChanges(true);
        }
        break;
      case 'html_content':
        if (suggestion.proposed_value) {
          setHtmlContent(prev => prev + '\n' + suggestion.proposed_value);
          setHasUnsavedChanges(true);
        }
        break;
      case 'faq':
        if (suggestion.proposed_value) {
          try {
            let newFaq;
            if (typeof suggestion.proposed_value === 'string') {
              newFaq = JSON.parse(suggestion.proposed_value);
            } else {
              newFaq = suggestion.proposed_value;
            }
            if (newFaq.question && newFaq.answer) {
              setArticle(prev => ({
                ...prev,
                faq: [...(prev.faq || []), newFaq]
              }));
              setHasUnsavedChanges(true);
            }
          } catch (e) {
            console.warn('Could not parse FAQ suggestion:', e);
          }
        }
        break;
      default:
        break;
    }
  };

  const handleHtmlChange = (e) => {
    setHtmlContent(e.target.value);
    setHasUnsavedChanges(true);
  };

  const handleVisualBlur = (e) => {
    setHtmlContent(e.target.innerHTML);
    setHasUnsavedChanges(true);
  };

  // --- Scheduling ---
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleWp, setScheduleWp] = useState(true);
  const [scheduling, setScheduling] = useState(false);

  const handleSchedule = async () => {
    if (!scheduleDate) { toast.error('Wybierz date publikacji'); return; }
    setScheduling(true);
    try {
      await axios.post(`${BACKEND_URL}/api/articles/${articleId}/schedule`, {
        scheduled_at: new Date(scheduleDate).toISOString(),
        publish_to_wordpress: scheduleWp
      });
      setArticle(prev => ({ ...prev, scheduled_at: new Date(scheduleDate).toISOString(), schedule_status: 'scheduled' }));
      toast.success('Publikacja zaplanowana');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad planowania');
    } finally {
      setScheduling(false);
    }
  };

  const handleCancelSchedule = async () => {
    try {
      await axios.delete(`${BACKEND_URL}/api/articles/${articleId}/schedule`);
      setArticle(prev => ({ ...prev, scheduled_at: null, schedule_status: null }));
      toast.success('Planowanie anulowane');
    } catch (err) {
      toast.error('Blad anulowania');
    }
  };

  // --- Linkbuilding ---
  const [linkSuggestions, setLinkSuggestions] = useState(null);
  const [linkLoading, setLinkLoading] = useState(false);
  const [compUrl, setCompUrl] = useState('');
  const [compResult, setCompResult] = useState(null);
  const [compLoading, setCompLoading] = useState(false);

  const handleAnalyzeLinks = async () => {
    setLinkLoading(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/linkbuilding`);
      setLinkSuggestions(res.data);
      toast.success('Analiza linkowania zakonczona');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad analizy linkowania');
    } finally {
      setLinkLoading(false);
    }
  };

  const handleCompetitionAnalysis = async () => {
    if (!compUrl) { toast.error('Podaj URL konkurencji'); return; }
    setCompLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      // Start async competition analysis
      const startRes = await axios.post(`${BACKEND_URL}/api/competition/analyze`, {
        article_id: articleId, competitor_url: compUrl
      }, { headers });
      const jobId = startRes.data.job_id;
      
      // Poll for result
      const poll = async () => {
        try {
          const statusRes = await axios.get(`${BACKEND_URL}/api/competition/status/${jobId}`, { headers });
          if (statusRes.data.status === 'completed') {
            setCompResult(statusRes.data.result);
            toast.success('Analiza konkurencji zakonczona');
            setCompLoading(false);
          } else if (statusRes.data.status === 'failed') {
            toast.error(statusRes.data.error || 'Blad analizy');
            setCompLoading(false);
          } else {
            setTimeout(poll, 2000);
          }
        } catch (e) {
          toast.error('Blad sprawdzania statusu');
          setCompLoading(false);
        }
      };
      setTimeout(poll, 2000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad analizy');
      setCompLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="editor-layout">
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Loader2 size={40} className="animate-spin" style={{ color: '#04389E' }} />
        </div>
      </div>
    );
  }

  if (!article) return null;

  return (
    <div className="editor-layout">
      {/* Left Panel - TOC */}
      <div className="editor-left-panel" data-testid="article-toc-panel">
        <div className="panel-section">
          <div className="panel-section-title">Spis treści</div>
          <TOCPanel 
            sections={article.sections || []} 
            toc={article.toc || []}
          />
        </div>
        
        <div className="panel-section">
          <div className="panel-section-title">Linkowanie wewnętrzne</div>
          {(article.internal_link_suggestions || []).map((link, idx) => (
            <div key={idx} style={{ padding: '6px 0', fontSize: 13, borderBottom: '1px solid hsl(214, 18%, 93%)' }}>
              <div style={{ fontWeight: 500, color: '#04389E' }}>{link.anchor_text}</div>
              <div style={{ color: 'hsl(215, 16%, 45%)', fontSize: 12, marginTop: 2 }}>{link.target_topic}</div>
            </div>
          ))}
        </div>

        <div className="panel-section">
          <div className="panel-section-title">Źródła</div>
          {(article.sources || []).map((src, idx) => (
            <div key={idx} style={{ padding: '6px 0', fontSize: 12, borderBottom: '1px solid hsl(214, 18%, 93%)' }}>
              <a href={src.url} target="_blank" rel="noopener noreferrer" style={{ color: '#04389E', textDecoration: 'none' }}>
                {src.name}
              </a>
              <span style={{ marginLeft: 6, color: 'hsl(215, 16%, 45%)' }}>({src.type})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Center - Editor */}
      <div className="editor-center">
        <div className="editor-toolbar">
          <div className="editor-toolbar-group">
            <button className="btn-icon" onClick={() => navigate('/')} title="Powrót">
              <ChevronLeft size={18} />
            </button>
            <h2>{article.title}</h2>
            {/* Autosave indicator */}
            {hasUnsavedChanges ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 8 }}>
                <CloudOff size={14} style={{ color: 'hsl(38, 92%, 45%)' }} />
                <span style={{ fontSize: 11, color: 'hsl(38, 92%, 45%)', fontWeight: 500 }}>Niezapisane</span>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 8 }}>
                <Cloud size={14} style={{ color: 'hsl(158, 55%, 34%)' }} />
                <span style={{ fontSize: 11, color: 'hsl(158, 55%, 34%)', fontWeight: 500 }}>Zapisano</span>
              </div>
            )}
          </div>
          <div className="editor-toolbar-group">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleRescore}
              disabled={scoring}
              className="gap-1"
            >
              {scoring ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Oblicz SEO
            </Button>
            <Button 
              size="sm" 
              onClick={handleSave}
              disabled={saving}
              data-testid="article-save-button"
              className="gap-1"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              Zapisz
            </Button>
          </div>
        </div>

        {/* Meta fields */}
        <div style={{ padding: '12px 20px', background: 'white', borderBottom: '1px solid hsl(214, 18%, 88%)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)' }}>Meta tytuł <span style={{ color: metaTitle.length > 60 ? 'hsl(0, 72%, 51%)' : 'hsl(215, 16%, 65%)' }}>({metaTitle.length}/60)</span></label>
                <button 
                  onClick={handleRegenerateMeta}
                  disabled={regenerating === 'meta'}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#04389E' }}
                  title="Regeneruj meta dane"
                >
                  {regenerating === 'meta' ? <Loader2 size={12} className="animate-spin" /> : <Wand2 size={12} />}
                  Regeneruj
                </button>
              </div>
              <Input
                value={metaTitle}
                onChange={handleMetaTitleChange}
                placeholder="Meta tytuł SEO"
                data-testid="meta-title-input"
                style={{ fontSize: 13 }}
              />
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)' }}>Meta opis <span style={{ color: metaDescription.length > 160 ? 'hsl(0, 72%, 51%)' : 'hsl(215, 16%, 65%)' }}>({metaDescription.length}/160)</span></label>
              </div>
              <Input
                value={metaDescription}
                onChange={handleMetaDescChange}
                placeholder="Meta opis SEO"
                data-testid="meta-description-textarea"
                style={{ fontSize: 13 }}
              />
            </div>
          </div>
        </div>

        {/* Editor tabs */}
        <div className="editor-tabs" data-testid="article-editor-tabs">
          <button 
            className={`editor-tab ${editorTab === 'visual' ? 'active' : ''}`}
            onClick={() => setEditorTab('visual')}
          >
            <Eye size={14} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            Wizualny
          </button>
          <button 
            className={`editor-tab ${editorTab === 'html' ? 'active' : ''}`}
            onClick={() => setEditorTab('html')}
          >
            <Code size={14} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            HTML
          </button>
        </div>

        <div className="editor-content-area">
          {editorTab === 'visual' ? (
            <>
              <EditorToolbar editorRef={editorContentRef} />
              <div 
                ref={editorContentRef}
                className="visual-editor-canvas"
                contentEditable
                suppressContentEditableWarning
                dangerouslySetInnerHTML={{ __html: htmlContent }}
                onBlur={handleVisualBlur}
                onInput={(e) => {
                  if (!hasUnsavedChanges) setHasUnsavedChanges(true);
                }}
                data-testid="article-visual-editor"
              />
            </>
          ) : (
            <div className="html-editor-area">
              <textarea
                className="html-editor-textarea"
                value={htmlContent}
                onChange={handleHtmlChange}
                data-testid="article-html-editor"
                spellCheck={false}
              />
            </div>
          )}
        </div>
      </div>

      {/* Right Panel */}
      <div className="editor-right-panel">
        <div className="right-panel-tabs">
          <button 
            className={`right-panel-tab ${rightTab === 'seo' ? 'active' : ''}`}
            onClick={() => setRightTab('seo')}
          >
            <BarChart3 size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            SEO
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'assistant' ? 'active' : ''}`}
            onClick={() => setRightTab('assistant')}
            data-testid="article-ai-assistant-tab"
          >
            <Sparkles size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            AI
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'faq' ? 'active' : ''}`}
            onClick={() => setRightTab('faq')}
          >
            FAQ
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'images' ? 'active' : ''}`}
            onClick={() => setRightTab('images')}
          >
            <ImageIcon size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            Obrazy
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'export' ? 'active' : ''}`}
            onClick={() => setRightTab('export')}
          >
            <Share2 size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            Eksport
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'links' ? 'active' : ''}`}
            onClick={() => setRightTab('links')}
          >
            <Link2 size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            Linki
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'schedule' ? 'active' : ''}`}
            onClick={() => setRightTab('schedule')}
          >
            <CalendarClock size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            Plan
          </button>
          <button 
            className={`right-panel-tab ${rightTab === 'chat' ? 'active' : ''}`}
            onClick={() => setRightTab('chat')}
            data-testid="article-chat-tab"
          >
            <MessageSquare size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            Chat
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          {rightTab === 'seo' && (
            <div data-testid="article-seo-panel">
              <SEOScorePanel 
                seoScore={article.seo_score} 
                onRescore={handleRescore}
                scoring={scoring}
              />
            </div>
          )}
          {rightTab === 'assistant' && (
            <div data-testid="article-ai-assistant-panel" style={{ height: '100%' }}>
              <SEOAssistantPanel
                articleId={articleId}
                article={article}
                onApplySuggestion={handleApplySuggestion}
              />
            </div>
          )}
          {rightTab === 'faq' && (
            <div data-testid="faq-accordion">
              <FAQEditor 
                faq={article.faq || []} 
                onChange={updateFAQ}
                onRegenerate={handleRegenerateFAQ}
                regenerating={regenerating === 'faq'}
              />
            </div>
          )}
          {rightTab === 'images' && (
            <div data-testid="article-images-panel">
              <ImageGenerator
                articleId={articleId}
                article={article}
                onInsertImage={(imgHtml) => {
                  setHtmlContent(prev => prev + '\n' + imgHtml);
                  setHasUnsavedChanges(true);
                }}
              />
            </div>
          )}
          {rightTab === 'export' && (
            <div data-testid="article-export-panel">
              <ExportPanel articleId={articleId} />
            </div>
          )}
          {rightTab === 'links' && (
            <div data-testid="article-links-panel" style={{ padding: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Linkowanie wewnetrzne</h3>
                <p style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)', marginBottom: 12 }}>
                  AI przeanalizuje wszystkie artykuly i zasugeruje linki wewnetrzne.
                </p>
                <Button onClick={handleAnalyzeLinks} disabled={linkLoading} className="gap-2 w-full" size="sm">
                  {linkLoading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  Analizuj linkowanie
                </Button>
              </div>
              {linkSuggestions && (
                <div>
                  {linkSuggestions.summary && (
                    <p style={{ fontSize: 12, color: '#04389E', background: 'hsl(220, 95%, 96%)', padding: '8px 12px', borderRadius: 8, marginBottom: 12 }}>
                      {linkSuggestions.summary}
                    </p>
                  )}
                  {(linkSuggestions.outgoing_links || []).length > 0 && (
                    <div style={{ marginBottom: 16 }}>
                      <h4 style={{ fontSize: 12, fontWeight: 700, color: 'hsl(215, 16%, 40%)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Linki wychodzace ({linkSuggestions.outgoing_links.length})
                      </h4>
                      {linkSuggestions.outgoing_links.map((link, i) => (
                        <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid hsl(214, 18%, 93%)', fontSize: 12 }}>
                          <div style={{ fontWeight: 600, color: '#04389E' }}>{link.anchor_text}</div>
                          <div style={{ color: 'hsl(215, 16%, 45%)', marginTop: 2 }}>{link.target_title}</div>
                          {link.context_sentence && (
                            <div style={{ color: 'hsl(215, 16%, 55%)', marginTop: 4, fontStyle: 'italic', fontSize: 11 }}
                              dangerouslySetInnerHTML={{ __html: link.context_sentence }} />
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  {(linkSuggestions.incoming_links || []).length > 0 && (
                    <div>
                      <h4 style={{ fontSize: 12, fontWeight: 700, color: 'hsl(215, 16%, 40%)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Linki przychodzace ({linkSuggestions.incoming_links.length})
                      </h4>
                      {linkSuggestions.incoming_links.map((link, i) => (
                        <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid hsl(214, 18%, 93%)', fontSize: 12 }}>
                          <div style={{ fontWeight: 600, color: 'hsl(142, 60%, 30%)' }}>{link.anchor_text}</div>
                          <div style={{ color: 'hsl(215, 16%, 45%)', marginTop: 2 }}>Z: {link.source_title}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              {/* Competition Analysis */}
              <div style={{ marginTop: 20, borderTop: '1px solid hsl(214, 18%, 90%)', paddingTop: 16 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Analiza konkurencji</h3>
                <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
                  <input value={compUrl} onChange={(e) => setCompUrl(e.target.value)}
                    placeholder="URL konkurenta"
                    data-testid="competition-url-input"
                    style={{ flex: 1, padding: '6px 10px', borderRadius: 6, border: '1px solid hsl(214, 18%, 85%)', fontSize: 12 }} />
                  <Button onClick={handleCompetitionAnalysis} disabled={compLoading} size="sm" style={{ flexShrink: 0 }}>
                    {compLoading ? <Loader2 size={12} className="animate-spin" /> : 'Porownaj'}
                  </Button>
                </div>
                {compResult && (
                  <div>
                    <div style={{
                      display: 'flex', gap: 8, marginBottom: 8
                    }}>
                      <div style={{
                        flex: 1, textAlign: 'center', padding: '8px', borderRadius: 8,
                        background: 'hsl(220, 95%, 96%)', fontSize: 12
                      }}>
                        <div style={{ fontWeight: 700, color: '#04389E', fontSize: 16 }}>{compResult.my_score || '?'}</div>
                        <div style={{ color: 'hsl(215, 16%, 50%)' }}>Twoj</div>
                      </div>
                      <div style={{
                        flex: 1, textAlign: 'center', padding: '8px', borderRadius: 8,
                        background: 'hsl(0, 0%, 96%)', fontSize: 12
                      }}>
                        <div style={{ fontWeight: 700, color: 'hsl(215, 16%, 35%)', fontSize: 16 }}>{compResult.competitor_score || '?'}</div>
                        <div style={{ color: 'hsl(215, 16%, 50%)' }}>Konkurent</div>
                      </div>
                    </div>
                    {compResult.summary && (
                      <p style={{ fontSize: 11, color: 'hsl(215, 16%, 40%)', marginBottom: 8, lineHeight: 1.4 }}>{compResult.summary}</p>
                    )}
                    {(compResult.action_plan || []).slice(0, 3).map((a, i) => (
                      <div key={i} style={{ fontSize: 11, padding: '4px 0', borderBottom: '1px solid hsl(214, 18%, 93%)' }}>
                        <span style={{ fontWeight: 700, color: '#04389E', marginRight: 4 }}>#{a.priority}</span>
                        {a.action}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
          {rightTab === 'schedule' && (
            <div data-testid="article-schedule-panel" style={{ padding: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Zaplanuj publikacje</h3>
              {article.schedule_status === 'scheduled' ? (
                <div style={{ background: 'hsl(220, 95%, 96%)', borderRadius: 10, padding: 16, marginBottom: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <CalendarClock size={16} style={{ color: '#04389E' }} />
                    <span style={{ fontWeight: 600, color: '#04389E', fontSize: 13 }}>Zaplanowano</span>
                  </div>
                  <p style={{ fontSize: 13, color: 'hsl(222, 47%, 25%)', marginBottom: 4 }}>
                    {article.scheduled_at ? new Date(article.scheduled_at).toLocaleString('pl-PL') : ''}
                  </p>
                  <p style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', marginBottom: 12 }}>
                    {article.scheduled_wp !== false ? 'Publikacja na WordPress' : 'Bez WordPress'}
                  </p>
                  <Button variant="outline" size="sm" onClick={handleCancelSchedule} className="w-full"
                    data-testid="cancel-schedule-btn">
                    Anuluj planowanie
                  </Button>
                </div>
              ) : (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <label style={{ fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 6 }}>Data i godzina</label>
                    <input
                      type="datetime-local"
                      value={scheduleDate}
                      onChange={(e) => setScheduleDate(e.target.value)}
                      data-testid="schedule-datetime-input"
                      style={{
                        width: '100%', padding: '8px 12px', borderRadius: 8,
                        border: '1px solid hsl(214, 18%, 85%)', fontSize: 13
                      }}
                    />
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, marginBottom: 16 }}>
                    <input type="checkbox" checked={scheduleWp} onChange={(e) => setScheduleWp(e.target.checked)}
                      data-testid="schedule-wp-checkbox" />
                    Publikuj rowniez na WordPress
                  </label>
                  <Button onClick={handleSchedule} disabled={scheduling} className="gap-2 w-full"
                    data-testid="schedule-publish-btn">
                    {scheduling ? <Loader2 size={14} className="animate-spin" /> : <CalendarClock size={14} />}
                    Zaplanuj publikacje
                  </Button>
                </div>
              )}
            </div>
          )}
          {rightTab === 'chat' && (
            <div data-testid="article-chat-panel-wrapper" style={{ height: '100%', padding: 0 }}>
              <AIChatPanel articleId={articleId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticleEditor;
