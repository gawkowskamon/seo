import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, Eye, Code, BarChart3, Share2, ChevronLeft, Loader2, RefreshCw, Wand2, Cloud, CloudOff, Image as ImageIcon, Sparkles } from 'lucide-react';
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
            <div 
              className="visual-editor-canvas"
              contentEditable
              suppressContentEditableWarning
              dangerouslySetInnerHTML={{ __html: htmlContent }}
              onBlur={handleVisualBlur}
              data-testid="article-visual-editor"
            />
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
        </div>
      </div>
    </div>
  );
};

export default ArticleEditor;
