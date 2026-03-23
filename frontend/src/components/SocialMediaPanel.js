import React, { useState, useCallback } from 'react';
import { Share2, Loader2, Copy, CheckCircle, Linkedin, Twitter, Facebook, Instagram, Star, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PLATFORMS = [
  { key: 'linkedin', label: 'LinkedIn', icon: Linkedin, color: '#0A66C2' },
  { key: 'twitter', label: 'Twitter / X', icon: Twitter, color: '#1DA1F2' },
  { key: 'facebook', label: 'Facebook', icon: Facebook, color: '#1877F2' },
  { key: 'instagram', label: 'Instagram', icon: Instagram, color: '#E4405F' },
];

const TONE_LABELS = { profesjonalny: 'Profesjonalny', zachęcający: 'Zachęcający', 'z pytaniem': 'Z pytaniem' };
const TONE_COLORS = { profesjonalny: '#04389E', zachęcający: '#16a34a', 'z pytaniem': '#f59e0b' };

const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast.success('Skopiowano do schowka');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      toast.success('Skopiowano do schowka');
      setTimeout(() => setCopied(false), 2000);
    }
  };
  return (
    <button className="social-copy-btn" onClick={handleCopy} data-testid="social-copy-button" title="Kopiuj">
      {copied ? <CheckCircle size={14} style={{ color: '#16a34a' }} /> : <Copy size={14} />}
    </button>
  );
};

const SocialMediaPanel = ({ articleId }) => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activePlatform, setActivePlatform] = useState('linkedin');
  const [expandedTips, setExpandedTips] = useState(false);

  const pollStatus = useCallback(async (jobId) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/social-posts/status/${jobId}`);
      if (res.data.status === 'completed') {
        setResult(res.data.result);
        setLoading(false);
        toast.success('Posty wygenerowane!');
      } else if (res.data.status === 'failed') {
        setLoading(false);
        toast.error(res.data.error || 'Błąd generowania');
      } else {
        setTimeout(() => pollStatus(jobId), 2500);
      }
    } catch {
      setLoading(false);
      toast.error('Błąd połączenia');
    }
  }, []);

  const generate = async () => {
    if (!articleId) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/social-posts`, { article_id: articleId });
      if (res.data.job_id) setTimeout(() => pollStatus(res.data.job_id), 2500);
    } catch {
      setLoading(false);
      toast.error('Błąd uruchamiania');
    }
  };

  const engagementColor = (e) => e === 'wysoki' ? '#16a34a' : e === 'średni' ? '#f59e0b' : '#94a3b8';

  return (
    <div className="plagiarism-panel" data-testid="social-media-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Share2 size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Social Media</span>
        </div>
        <Button size="sm" onClick={generate} disabled={loading || !articleId} className="gap-1" data-testid="social-generate-button">
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Share2 size={14} />}
          {loading ? 'Generuję...' : 'Generuj posty'}
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={24} className="animate-spin" style={{ color: '#04389E' }} />
          <p>AI tworzy posty na 4 platformy w 3 tonach...</p>
        </div>
      )}

      {result && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Platform tabs */}
          <div className="social-platform-tabs" data-testid="social-platform-tabs">
            {PLATFORMS.map(p => (
              <button
                key={p.key}
                className={`social-platform-tab ${activePlatform === p.key ? 'active' : ''}`}
                onClick={() => setActivePlatform(p.key)}
                style={activePlatform === p.key ? { borderBottomColor: p.color, color: p.color } : {}}
                data-testid={`social-tab-${p.key}`}
              >
                <p.icon size={14} /> {p.label}
              </button>
            ))}
          </div>

          {/* Posts for selected platform */}
          <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {(result[activePlatform] || []).map((post, idx) => (
              <div key={idx} className="social-post-card" data-testid="social-post-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span className="social-tone-badge" style={{ background: `${TONE_COLORS[post.tone] || '#94a3b8'}12`, color: TONE_COLORS[post.tone] || '#94a3b8', border: `1px solid ${TONE_COLORS[post.tone] || '#94a3b8'}30` }}>
                    {TONE_LABELS[post.tone] || post.tone}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span className="social-engagement" style={{ color: engagementColor(post.estimated_engagement) }}>
                      {post.estimated_engagement}
                    </span>
                    <CopyButton text={post.text} />
                  </div>
                </div>
                <div className="social-post-text">{post.text}</div>
                {post.hashtags?.length > 0 && (
                  <div className="social-hashtags">
                    {post.hashtags.slice(0, 10).map((h, i) => (
                      <span key={i} className="social-hashtag">{h}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {(!result[activePlatform] || result[activePlatform].length === 0) && (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 12, padding: 16 }}>Brak postów dla tej platformy</p>
            )}
          </div>

          {/* Tips */}
          {result.tips?.length > 0 && (
            <div style={{ padding: '0 12px 12px' }}>
              <button className="plagiarism-toggle" onClick={() => setExpandedTips(!expandedTips)}>
                {expandedTips ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                <Star size={13} style={{ marginRight: 2 }} /> Porady ({result.tips.length})
              </button>
              {expandedTips && (
                <div className="plagiarism-recs" style={{ marginTop: 4 }}>
                  <ul>
                    {result.tips.map((t, i) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!result && !loading && (
        <p className="plagiarism-hint">AI wygeneruje gotowe posty na LinkedIn, Twitter, Facebook i Instagram w 3 tonach — do skopiowania jednym kliknięciem.</p>
      )}
    </div>
  );
};

export default SocialMediaPanel;
