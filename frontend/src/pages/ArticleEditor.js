import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Save, RotateCcw, Eye, Code, BarChart3, Share2, ChevronLeft, Loader2, Copy, Download, RefreshCw, Plus, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import SEOScorePanel from '../components/SEOScorePanel';
import ExportPanel from '../components/ExportPanel';
import FAQEditor from '../components/FAQEditor';
import TOCPanel from '../components/TOCPanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ArticleEditor = () => {
  const { articleId } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [scoring, setScoring] = useState(false);
  
  // Editor state
  const [editorTab, setEditorTab] = useState('visual'); // visual, html
  const [rightTab, setRightTab] = useState('seo'); // seo, export, faq
  const [htmlContent, setHtmlContent] = useState('');
  
  // Meta editing
  const [metaTitle, setMetaTitle] = useState('');
  const [metaDescription, setMetaDescription] = useState('');

  useEffect(() => {
    fetchArticle();
  }, [articleId]);

  const fetchArticle = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/articles/${articleId}`);
      setArticle(response.data);
      setHtmlContent(buildHtmlFromArticle(response.data));
      setMetaTitle(response.data.meta_title || '');
      setMetaDescription(response.data.meta_description || '');
    } catch (error) {
      toast.error('B\u0142\u0105d podczas \u0142adowania artyku\u0142u');
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
    
    // FAQ
    if (art.faq && art.faq.length > 0) {
      html += `<h2>FAQ</h2>\n`;
      for (const faq of art.faq) {
        html += `<h3>${faq.question}</h3>\n`;
        html += `<p>${faq.answer}</p>\n\n`;
      }
    }
    
    return html;
  };

  const handleSave = async () => {
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
      toast.success('Artyku\u0142 zapisany');
    } catch (error) {
      toast.error('B\u0142\u0105d podczas zapisywania');
    } finally {
      setSaving(false);
    }
  };

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
      toast.error('B\u0142\u0105d podczas obliczania wyniku');
    } finally {
      setScoring(false);
    }
  };

  const updateFAQ = (newFaq) => {
    setArticle(prev => ({ ...prev, faq: newFaq }));
  };

  const updateSections = (newSections) => {
    setArticle(prev => ({ ...prev, sections: newSections }));
    setHtmlContent(buildHtmlFromArticle({ ...article, sections: newSections }));
  };

  if (loading) {
    return (
      <div className="editor-layout">
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Loader2 size={40} className="animate-spin" style={{ color: 'hsl(209, 88%, 36%)' }} />
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
          <div className="panel-section-title">Spis tre\u015bci</div>
          <TOCPanel 
            sections={article.sections || []} 
            toc={article.toc || []}
          />
        </div>
        
        <div className="panel-section">
          <div className="panel-section-title">Linkowanie wewn\u0119trzne</div>
          {(article.internal_link_suggestions || []).map((link, idx) => (
            <div key={idx} style={{ padding: '6px 0', fontSize: 13, borderBottom: '1px solid hsl(214, 18%, 93%)' }}>
              <div style={{ fontWeight: 500, color: 'hsl(209, 88%, 36%)' }}>{link.anchor_text}</div>
              <div style={{ color: 'hsl(215, 16%, 45%)', fontSize: 12, marginTop: 2 }}>{link.target_topic}</div>
            </div>
          ))}
        </div>

        <div className="panel-section">
          <div className="panel-section-title">Źr\u00f3d\u0142a</div>
          {(article.sources || []).map((src, idx) => (
            <div key={idx} style={{ padding: '6px 0', fontSize: 12, borderBottom: '1px solid hsl(214, 18%, 93%)' }}>
              <a href={src.url} target="_blank" rel="noopener noreferrer" style={{ color: 'hsl(209, 88%, 36%)', textDecoration: 'none' }}>
                {src.name}
              </a>
              <span style={{ marginLeft: 6, color: 'hsl(215, 16%, 45%)' }}>({src.type})</span>
            </div>
          ))}
        </div>
      </div>

      {/* Center - Editor */}
      <div className="editor-center">
        {/* Toolbar */}
        <div className="editor-toolbar">
          <div className="editor-toolbar-group">
            <button className="btn-icon" onClick={() => navigate('/')} title="Powr\u00f3t">
              <ChevronLeft size={18} />
            </button>
            <h2>{article.title}</h2>
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
              <label style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)', display: 'block', marginBottom: 4 }}>Meta tytu\u0142 <span style={{ color: 'hsl(215, 16%, 65%)' }}>({metaTitle.length}/60)</span></label>
              <Input
                value={metaTitle}
                onChange={(e) => setMetaTitle(e.target.value)}
                placeholder="Meta tytu\u0142 SEO"
                data-testid="meta-title-input"
                style={{ fontSize: 13 }}
              />
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)', display: 'block', marginBottom: 4 }}>Meta opis <span style={{ color: 'hsl(215, 16%, 65%)' }}>({metaDescription.length}/160)</span></label>
              <Input
                value={metaDescription}
                onChange={(e) => setMetaDescription(e.target.value)}
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

        {/* Editor content */}
        <div className="editor-content-area">
          {editorTab === 'visual' ? (
            <div 
              className="visual-editor-canvas"
              contentEditable
              suppressContentEditableWarning
              dangerouslySetInnerHTML={{ __html: htmlContent }}
              onBlur={(e) => setHtmlContent(e.target.innerHTML)}
              data-testid="article-visual-editor"
            />
          ) : (
            <div className="html-editor-area">
              <textarea
                className="html-editor-textarea"
                value={htmlContent}
                onChange={(e) => setHtmlContent(e.target.value)}
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
            className={`right-panel-tab ${rightTab === 'faq' ? 'active' : ''}`}
            onClick={() => setRightTab('faq')}
          >
            FAQ
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
          {rightTab === 'faq' && (
            <div data-testid="faq-accordion">
              <FAQEditor 
                faq={article.faq || []} 
                onChange={updateFAQ} 
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
