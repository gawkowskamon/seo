import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Loader2, Trash2, Bot, User } from 'lucide-react';
import { Button } from './ui/button';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function AIChatPanel({ articleId }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Czesc! Jestem Twoim asystentem AI. Moge pomoc Ci z artykulem - poprawic SEO, napisac nowe sekcje, wygenerowac FAQ lub odpowiedziec na pytania o przepisy podatkowe. Jak moge pomoc?' }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;
    
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInput('');
    setSending(true);
    
    try {
      const res = await axios.post(`${BACKEND_URL}/api/chat/message`, {
        message: text,
        article_id: articleId || ''
      }, { timeout: 60000 });
      
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Przepraszam, wystapil blad. Sprobuj ponownie.' }]);
    } finally {
      setSending(false);
    }
  };

  const handleClear = async () => {
    setMessages([{ role: 'assistant', content: 'Historia czatu wyczyszczona. Jak moge pomoc?' }]);
    try { await axios.post(`${BACKEND_URL}/api/chat/clear`); } catch (e) {}
  };

  const quickActions = [
    'Popraw SEO tego artykulu',
    'Dodaj FAQ o podatkach',
    'Zaproponuj lepszy tytul',
    'Uprość jezyk artykulu'
  ];

  return (
    <div data-testid="ai-chat-panel" style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'white', borderRadius: 14, border: '1px solid #E2E8F0',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #E2E8F0',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: '#F8FAFC'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: 'linear-gradient(135deg, #04389E 0%, #0652D0 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Bot size={15} style={{ color: 'white' }} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 13, color: '#0B1220' }}>Asystent AI</span>
        </div>
        <button onClick={handleClear} data-testid="chat-clear-btn"
          style={{
            padding: '4px 8px', borderRadius: 6, border: '1px solid #E2E8F0',
            background: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
            fontSize: 11, color: '#64748B'
          }}>
          <Trash2 size={11} /> Wyczysc
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{
        flex: 1, overflowY: 'auto', padding: 12, display: 'flex',
        flexDirection: 'column', gap: 10, minHeight: 200, maxHeight: 400
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex', gap: 8,
            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
          }}>
            <div style={{
              width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
              background: msg.role === 'user' ? '#04389E' : '#F1F5F9',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginTop: 2
            }}>
              {msg.role === 'user' 
                ? <User size={12} style={{ color: 'white' }} />
                : <Bot size={12} style={{ color: '#04389E' }} />
              }
            </div>
            <div style={{
              maxWidth: '85%', padding: '8px 12px', borderRadius: 12,
              fontSize: 13, lineHeight: 1.5,
              background: msg.role === 'user' ? '#04389E' : '#F1F5F9',
              color: msg.role === 'user' ? 'white' : '#0B1220',
              borderBottomRightRadius: msg.role === 'user' ? 4 : 12,
              borderBottomLeftRadius: msg.role === 'user' ? 12 : 4
            }}
            dangerouslySetInnerHTML={{ __html: msg.content }}
            />
          </div>
        ))}
        {sending && (
          <div style={{ display: 'flex', gap: 8 }}>
            <div style={{
              width: 24, height: 24, borderRadius: '50%',
              background: '#F1F5F9', display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Bot size={12} style={{ color: '#04389E' }} />
            </div>
            <div style={{
              padding: '8px 12px', borderRadius: 12, background: '#F1F5F9',
              display: 'flex', alignItems: 'center', gap: 6
            }}>
              <Loader2 size={14} className="animate-spin" style={{ color: '#04389E' }} />
              <span style={{ fontSize: 12, color: '#64748B' }}>Pisze...</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick actions */}
      {messages.length <= 1 && (
        <div style={{
          padding: '0 12px 8px', display: 'flex', flexWrap: 'wrap', gap: 4
        }}>
          {quickActions.map((action, i) => (
            <button key={i} onClick={() => { setInput(action); }}
              style={{
                padding: '4px 10px', borderRadius: 16, fontSize: 11,
                border: '1px solid #E2E8F0', background: '#FAFBFC',
                cursor: 'pointer', color: '#64748B', fontWeight: 500,
                transition: 'all 0.12s'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#04389E'; e.currentTarget.style.color = '#04389E'; }}
              onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#E2E8F0'; e.currentTarget.style.color = '#64748B'; }}
            >
              {action}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: '8px 12px', borderTop: '1px solid #E2E8F0',
        display: 'flex', gap: 6, background: '#FAFBFC'
      }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Napisz wiadomosc..."
          data-testid="chat-input"
          style={{
            flex: 1, padding: '8px 12px', borderRadius: 10,
            border: '1px solid #E2E8F0', fontSize: 13,
            outline: 'none', background: 'white'
          }}
          disabled={sending}
        />
        <Button onClick={handleSend} disabled={sending || !input.trim()} size="sm"
          data-testid="chat-send-btn"
          style={{ borderRadius: 10, padding: '0 12px' }}>
          {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
        </Button>
      </div>
    </div>
  );
}
