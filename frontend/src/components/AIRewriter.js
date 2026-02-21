import React, { useState } from 'react';
import { RefreshCw, Loader2, Copy, Check, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const rewriteStyles = [
  { id: 'profesjonalny', label: 'Profesjonalny', icon: '1' },
  { id: 'przystępny', label: 'Przystępny', icon: '2' },
  { id: 'ekspercki', label: 'Ekspercki', icon: '3' },
  { id: 'seo', label: 'SEO', icon: '4' },
  { id: 'skrócony', label: 'Skróć', icon: '5' },
  { id: 'rozszerzony', label: 'Rozszerz', icon: '6' },
];

export default function AIRewriter({ selectedText, onApply }) {
  const [style, setStyle] = useState('profesjonalny');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [copied, setCopied] = useState(false);
  const [customText, setCustomText] = useState('');

  const textToRewrite = selectedText || customText;

  const handleRewrite = async () => {
    if (!textToRewrite.trim()) {
      toast.error('Wklej lub zaznacz tekst do przepisania');
      return;
    }
    setLoading(true);
    setResult('');
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const startRes = await axios.post(`${BACKEND_URL}/api/rewrite`, {
        text: textToRewrite, style
      }, { headers });
      const jobId = startRes.data.job_id;

      const poll = async () => {
        const statusRes = await axios.get(`${BACKEND_URL}/api/rewrite/status/${jobId}`, { headers });
        if (statusRes.data.status === 'completed') {
          setResult(statusRes.data.result.rewritten_text);
          toast.success('Tekst przepisany');
          setLoading(false);
        } else if (statusRes.data.status === 'failed') {
          toast.error(statusRes.data.error || 'Błąd przepisywania');
          setLoading(false);
        } else {
          setTimeout(poll, 1500);
        }
      };
      setTimeout(poll, 1500);
    } catch (err) {
      toast.error('Błąd przepisywania tekstu');
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    toast.success('Skopiowano');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div data-testid="ai-rewriter-panel" style={{ padding: 16, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12,
        padding: '0 0 12px', borderBottom: '1px solid var(--border)'
      }}>
        <RefreshCw size={16} style={{ color: 'var(--accent)' }} />
        <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>AI Rewriter</span>
      </div>

      {/* Style selection */}
      <div style={{ marginBottom: 12 }}>
        <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
          Styl przepisania
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4 }}>
          {rewriteStyles.map(s => (
            <button key={s.id}
              onClick={() => setStyle(s.id)}
              data-testid={`rewriter-style-${s.id}`}
              style={{
                padding: '6px 4px', borderRadius: 8, fontSize: 11, fontWeight: 600,
                border: '1.5px solid', cursor: 'pointer', transition: 'all 0.12s',
                borderColor: style === s.id ? 'var(--accent)' : 'var(--border)',
                background: style === s.id ? 'rgba(4,56,158,0.08)' : 'var(--bg-card)',
                color: style === s.id ? 'var(--accent)' : 'var(--text-secondary)'
              }}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Input text */}
      {!selectedText && (
        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
            Tekst do przepisania
          </label>
          <textarea
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="Wklej tekst lub zaznacz fragment w edytorze..."
            data-testid="rewriter-input"
            rows={4}
            style={{
              width: '100%', padding: '8px 12px', borderRadius: 10,
              border: '1px solid var(--border)', fontSize: 12, resize: 'vertical',
              background: 'var(--bg-input)', color: 'var(--text-primary)',
              outline: 'none', lineHeight: 1.5
            }}
          />
        </div>
      )}

      {selectedText && (
        <div style={{
          padding: '8px 12px', borderRadius: 8, background: 'var(--bg-hover)',
          fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12,
          maxHeight: 80, overflowY: 'auto', lineHeight: 1.4
        }}>
          <span style={{ fontWeight: 600, fontSize: 10, color: 'var(--accent)' }}>ZAZNACZONY TEKST:</span><br />
          {selectedText.slice(0, 200)}{selectedText.length > 200 ? '...' : ''}
        </div>
      )}

      <Button onClick={handleRewrite} disabled={loading || !textToRewrite.trim()} className="w-full gap-2 mb-3"
        data-testid="rewrite-btn" size="sm">
        {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
        Przepisz tekst
      </Button>

      {/* Result */}
      {result && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6
          }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)' }}>WYNIK</span>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={handleCopy} data-testid="rewriter-copy-btn"
                style={{
                  padding: '3px 8px', borderRadius: 6, border: '1px solid var(--border)',
                  background: 'var(--bg-card)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 3,
                  fontSize: 10, color: 'var(--text-secondary)'
                }}>
                {copied ? <Check size={10} /> : <Copy size={10} />} Kopiuj
              </button>
              {onApply && (
                <button onClick={() => onApply(result)} data-testid="rewriter-apply-btn"
                  style={{
                    padding: '3px 8px', borderRadius: 6, border: '1px solid var(--accent)',
                    background: 'rgba(4,56,158,0.08)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 3,
                    fontSize: 10, color: 'var(--accent)', fontWeight: 600
                  }}>
                  <ArrowRight size={10} /> Zastosuj
                </button>
              )}
            </div>
          </div>
          <div style={{
            flex: 1, padding: '10px 12px', borderRadius: 10,
            border: '1px solid var(--border)', background: 'var(--bg-muted)',
            fontSize: 12, lineHeight: 1.6, overflowY: 'auto',
            color: 'var(--text-primary)', maxHeight: 250
          }}
          dangerouslySetInnerHTML={{ __html: result }}
          />
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Loader2 size={20} className="animate-spin" style={{ color: 'var(--accent)', marginBottom: 8 }} />
          <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Przepisuję tekst w stylu: {style}...</p>
        </div>
      )}
    </div>
  );
}
