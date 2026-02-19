import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Send, Loader2, ArrowRight, CheckCircle2, AlertTriangle, Info, ChevronDown, ChevronUp, Zap, MessageSquare, RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const IMPACT_CONFIG = {
  high: { label: 'Wysoki', color: 'hsl(0, 72%, 51%)', bg: 'hsl(0, 72%, 96%)', border: 'hsl(0, 72%, 88%)' },
  medium: { label: 'Sredni', color: 'hsl(38, 92%, 40%)', bg: 'hsl(38, 92%, 95%)', border: 'hsl(38, 80%, 80%)' },
  low: { label: 'Niski', color: 'hsl(209, 88%, 36%)', bg: 'hsl(209, 88%, 96%)', border: 'hsl(209, 60%, 85%)' },
};

const CATEGORY_LABELS = {
  meta: 'Meta dane',
  headings: 'Naglowki',
  content: 'Tresc',
  keywords: 'Slowa kluczowe',
  faq: 'FAQ',
  links: 'Linkowanie',
  readability: 'Czytelnosc',
};

const SEOAssistantPanel = ({ articleId, article, onApplySuggestion }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [expandedSuggestion, setExpandedSuggestion] = useState(null);
  const [appliedSuggestions, setAppliedSuggestions] = useState(new Set());
  const [activeView, setActiveView] = useState('suggestions');
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setSuggestions([]);
    setAppliedSuggestions(new Set());
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/articles/${articleId}/seo-assistant`,
        { mode: 'analyze' },
        { timeout: 120000 }
      );
      const data = response.data;
      setSuggestions(data.suggestions || []);
      if (data.assistant_message) {
        setChatMessages(prev => [
          ...prev,
          { role: 'assistant', content: data.assistant_message }
        ]);
      }
      toast.success('Analiza SEO zakonczona');
    } catch (error) {
      const msg = error.response?.data?.detail || 'Blad analizy SEO';
      toast.error(msg);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    const userMsg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setChatLoading(true);
    
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/articles/${articleId}/seo-assistant`,
        {
          mode: 'chat',
          message: userMsg,
          history: chatMessages.slice(-10)
        },
        { timeout: 120000 }
      );
      const data = response.data;
      
      setChatMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.assistant_message || 'Brak odpowiedzi.' }
      ]);
      
      if (data.suggestions && data.suggestions.length > 0) {
        setSuggestions(prev => {
          const existingIds = new Set(prev.map(s => s.id));
          const newSuggestions = data.suggestions.filter(s => !existingIds.has(s.id));
          return [...newSuggestions, ...prev];
        });
        toast.success(`${data.suggestions.length} nowych sugestii dodanych`);
      }
    } catch (error) {
      const msg = error.response?.data?.detail || 'Blad komunikacji z asystentem';
      setChatMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Przepraszam, wystapil blad: ${msg}` }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChat();
    }
  };

  const handleApply = (suggestion) => {
    if (onApplySuggestion) {
      onApplySuggestion(suggestion);
      setAppliedSuggestions(prev => new Set([...prev, suggestion.id]));
      toast.success(`Zastosowano: ${suggestion.title}`);
    }
  };

  const toggleSuggestion = (id) => {
    setExpandedSuggestion(expandedSuggestion === id ? null : id);
  };

  const activeSuggestions = suggestions.filter(s => !appliedSuggestions.has(s.id));
  const appliedList = suggestions.filter(s => appliedSuggestions.has(s.id));

  return (
    <div data-testid="ai-assistant-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="panel-section" style={{ paddingBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Sparkles size={16} style={{ color: 'hsl(209, 88%, 36%)' }} />
          <span style={{ fontSize: 13, fontWeight: 700, color: 'hsl(222, 47%, 11%)' }}>Asystent SEO AI</span>
          <Badge variant="outline" style={{ fontSize: 10, padding: '1px 6px', marginLeft: 'auto' }}>GPT-5.2</Badge>
        </div>
        <Button
          onClick={handleAnalyze}
          disabled={analyzing}
          size="sm"
          className="gap-1 w-full"
          data-testid="ai-assistant-analyze-button"
        >
          {analyzing ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              Analizowanie artykulu...
            </>
          ) : (
            <>
              <Zap size={14} />
              Analizuj artykul
            </>
          )}
        </Button>
      </div>

      {/* View Toggle */}
      <div style={{ display: 'flex', borderBottom: '1px solid hsl(214, 18%, 88%)' }}>
        <button
          onClick={() => setActiveView('suggestions')}
          style={{
            flex: 1,
            padding: '8px 12px',
            fontSize: 12,
            fontWeight: 600,
            color: activeView === 'suggestions' ? 'hsl(209, 88%, 36%)' : 'hsl(215, 16%, 45%)',
            borderBottom: activeView === 'suggestions' ? '2px solid hsl(209, 88%, 36%)' : '2px solid transparent',
            background: 'none',
            border: 'none',
            borderBottomWidth: 2,
            borderBottomStyle: 'solid',
            borderBottomColor: activeView === 'suggestions' ? 'hsl(209, 88%, 36%)' : 'transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            transition: 'color 0.15s'
          }}
          data-testid="ai-assistant-suggestions-tab"
        >
          <Zap size={12} />
          Sugestie {activeSuggestions.length > 0 && `(${activeSuggestions.length})`}
        </button>
        <button
          onClick={() => setActiveView('chat')}
          style={{
            flex: 1,
            padding: '8px 12px',
            fontSize: 12,
            fontWeight: 600,
            color: activeView === 'chat' ? 'hsl(209, 88%, 36%)' : 'hsl(215, 16%, 45%)',
            background: 'none',
            border: 'none',
            borderBottomWidth: 2,
            borderBottomStyle: 'solid',
            borderBottomColor: activeView === 'chat' ? 'hsl(209, 88%, 36%)' : 'transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            transition: 'color 0.15s'
          }}
          data-testid="ai-assistant-chat-tab"
        >
          <MessageSquare size={12} />
          Chat
        </button>
      </div>

      {/* Content area */}
      <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
        {activeView === 'suggestions' ? (
          <div data-testid="ai-assistant-suggestions">
            {suggestions.length === 0 && !analyzing ? (
              <div style={{ padding: '32px 20px', textAlign: 'center' }}>
                <Sparkles size={32} style={{ color: 'hsl(215, 16%, 75%)', margin: '0 auto 12px', display: 'block' }} />
                <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', lineHeight: 1.5 }}>
                  Kliknij "Analizuj artykul" aby uzyskac sugestie poprawy SEO.
                </p>
              </div>
            ) : analyzing ? (
              <div style={{ padding: '32px 20px', textAlign: 'center' }}>
                <Loader2 size={28} className="animate-spin" style={{ color: 'hsl(209, 88%, 36%)', margin: '0 auto 12px', display: 'block' }} />
                <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)' }}>GPT-5.2 analizuje Twoj artykul...</p>
                <p style={{ fontSize: 11, color: 'hsl(215, 16%, 65%)', marginTop: 4 }}>To moze potrwac 15-30 sekund</p>
              </div>
            ) : (
              <>
                {/* Active Suggestions */}
                {activeSuggestions.map((suggestion) => {
                  const impact = IMPACT_CONFIG[suggestion.impact] || IMPACT_CONFIG.low;
                  const catLabel = CATEGORY_LABELS[suggestion.category] || suggestion.category;
                  const isExpanded = expandedSuggestion === suggestion.id;
                  const canApply = suggestion.apply_target && suggestion.apply_target !== 'none' && suggestion.proposed_value;

                  return (
                    <div
                      key={suggestion.id}
                      style={{
                        padding: '12px 16px',
                        borderBottom: '1px solid hsl(214, 18%, 93%)',
                        transition: 'background-color 0.15s'
                      }}
                      data-testid="ai-suggestion-item"
                    >
                      <div
                        onClick={() => toggleSuggestion(suggestion.id)}
                        style={{ cursor: 'pointer', display: 'flex', alignItems: 'flex-start', gap: 8 }}
                      >
                        <div style={{
                          width: 6, height: 6, borderRadius: '50%',
                          background: impact.color,
                          marginTop: 6, flexShrink: 0
                        }} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', lineHeight: 1.3 }}>
                            {suggestion.title}
                          </div>
                          <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
                            <span style={{
                              fontSize: 10, fontWeight: 600,
                              padding: '1px 6px', borderRadius: 4,
                              background: impact.bg, color: impact.color,
                              border: `1px solid ${impact.border}`
                            }}>
                              {impact.label}
                            </span>
                            <span style={{
                              fontSize: 10, fontWeight: 500,
                              padding: '1px 6px', borderRadius: 4,
                              background: 'hsl(210, 22%, 96%)',
                              color: 'hsl(215, 16%, 45%)'
                            }}>
                              {catLabel}
                            </span>
                          </div>
                        </div>
                        {isExpanded ? <ChevronUp size={14} style={{ color: 'hsl(215, 16%, 65%)', flexShrink: 0 }} /> : <ChevronDown size={14} style={{ color: 'hsl(215, 16%, 65%)', flexShrink: 0 }} />}
                      </div>

                      {isExpanded && (
                        <div style={{ marginTop: 10, marginLeft: 14 }}>
                          <p style={{ fontSize: 12, color: 'hsl(215, 16%, 45%)', lineHeight: 1.5, marginBottom: 8 }}>
                            {suggestion.rationale}
                          </p>

                          {suggestion.current_value && (
                            <div style={{
                              fontSize: 11, padding: '6px 10px', borderRadius: 6,
                              background: 'hsl(0, 72%, 97%)', border: '1px solid hsl(0, 72%, 90%)',
                              marginBottom: 6, color: 'hsl(0, 50%, 35%)', lineHeight: 1.4
                            }}>
                              <strong>Obecnie:</strong> {suggestion.current_value.length > 150 ? suggestion.current_value.slice(0, 150) + '...' : suggestion.current_value}
                            </div>
                          )}

                          {suggestion.proposed_value && (
                            <div style={{
                              fontSize: 11, padding: '6px 10px', borderRadius: 6,
                              background: 'hsl(158, 55%, 96%)', border: '1px solid hsl(158, 55%, 85%)',
                              marginBottom: 8, color: 'hsl(158, 40%, 25%)', lineHeight: 1.4
                            }}>
                              <strong>Proponowana zmiana:</strong> {suggestion.proposed_value.length > 200 ? suggestion.proposed_value.slice(0, 200) + '...' : suggestion.proposed_value}
                            </div>
                          )}

                          {canApply && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => { e.stopPropagation(); handleApply(suggestion); }}
                              className="gap-1"
                              style={{ fontSize: 12 }}
                              data-testid="ai-assistant-apply-suggestion-button"
                            >
                              <ArrowRight size={12} />
                              Zastosuj
                            </Button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Applied Suggestions */}
                {appliedList.length > 0 && (
                  <div style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'hsl(158, 55%, 34%)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                      Zastosowane ({appliedList.length})
                    </div>
                    {appliedList.map((s) => (
                      <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0', fontSize: 12, color: 'hsl(215, 16%, 55%)' }}>
                        <CheckCircle2 size={12} style={{ color: 'hsl(158, 55%, 34%)' }} />
                        <span style={{ textDecoration: 'line-through' }}>{s.title}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          /* Chat View */
          <div data-testid="ai-assistant-chat" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px' }}>
              {chatMessages.length === 0 ? (
                <div style={{ padding: '24px 0', textAlign: 'center' }}>
                  <MessageSquare size={28} style={{ color: 'hsl(215, 16%, 75%)', margin: '0 auto 10px', display: 'block' }} />
                  <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', lineHeight: 1.5 }}>
                    Zapytaj asystenta o poprawe SEO artykulu.
                  </p>
                  <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {['Jak poprawic CTR meta opisu?', 'Zaproponuj lepsze naglowki H2', 'Jak zwiekszyc gestosc slow kluczowych?'].map((q, i) => (
                      <button
                        key={i}
                        onClick={() => { setChatInput(q); inputRef.current?.focus(); }}
                        style={{
                          fontSize: 11,
                          padding: '6px 10px',
                          borderRadius: 8,
                          border: '1px solid hsl(214, 18%, 88%)',
                          background: 'hsl(210, 22%, 98%)',
                          color: 'hsl(209, 88%, 36%)',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'background-color 0.15s'
                        }}
                        data-testid="ai-assistant-quick-question"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    style={{
                      marginBottom: 12,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}
                  >
                    <div style={{
                      fontSize: 10,
                      fontWeight: 600,
                      color: 'hsl(215, 16%, 55%)',
                      marginBottom: 3,
                      textTransform: 'uppercase',
                      letterSpacing: 0.3
                    }}>
                      {msg.role === 'user' ? 'Ty' : 'Asystent AI'}
                    </div>
                    <div style={{
                      fontSize: 13,
                      lineHeight: 1.5,
                      padding: '8px 12px',
                      borderRadius: 10,
                      maxWidth: '90%',
                      ...(msg.role === 'user' ? {
                        background: 'hsl(209, 88%, 36%)',
                        color: 'white',
                        borderBottomRightRadius: 4
                      } : {
                        background: 'hsl(210, 22%, 96%)',
                        color: 'hsl(222, 47%, 15%)',
                        borderBottomLeftRadius: 4,
                        border: '1px solid hsl(214, 18%, 90%)'
                      })
                    }}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {chatLoading && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 0' }}>
                  <Loader2 size={14} className="animate-spin" style={{ color: 'hsl(209, 88%, 36%)' }} />
                  <span style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)' }}>Asystent pisze...</span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Chat Input - always visible when chat tab is active */}
      {activeView === 'chat' && (
        <div style={{
          padding: '10px 12px',
          borderTop: '1px solid hsl(214, 18%, 88%)',
          background: 'white',
          display: 'flex',
          gap: 6,
          alignItems: 'flex-end'
        }}>
          <textarea
            ref={inputRef}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Zapytaj o poprawe SEO..."
            rows={1}
            style={{
              flex: 1,
              fontSize: 13,
              padding: '8px 12px',
              borderRadius: 8,
              border: '1px solid hsl(214, 18%, 88%)',
              resize: 'none',
              outline: 'none',
              fontFamily: 'inherit',
              lineHeight: 1.4,
              minHeight: 36,
              maxHeight: 80
            }}
            data-testid="ai-assistant-chat-input"
          />
          <Button
            size="sm"
            onClick={handleChat}
            disabled={chatLoading || !chatInput.trim()}
            style={{ minWidth: 36, height: 36, padding: 0 }}
            data-testid="ai-assistant-chat-send-button"
          >
            {chatLoading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          </Button>
        </div>
      )}
    </div>
  );
};

export default SEOAssistantPanel;
