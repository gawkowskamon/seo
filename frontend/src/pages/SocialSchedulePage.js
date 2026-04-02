import React, { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Linkedin, Twitter, Facebook, Instagram, Loader2, Trash2, CheckCircle, Clock, Plus, Copy, ExternalLink } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PLATFORMS = {
  linkedin: { label: 'LinkedIn', icon: Linkedin, color: '#0A66C2' },
  twitter: { label: 'Twitter / X', icon: Twitter, color: '#1DA1F2' },
  facebook: { label: 'Facebook', icon: Facebook, color: '#1877F2' },
  instagram: { label: 'Instagram', icon: Instagram, color: '#E4405F' },
};

const StatusBadge = ({ status }) => {
  const cfg = status === 'published'
    ? { bg: '#22c55e15', color: '#22c55e', label: 'Opublikowany' }
    : { bg: '#f59e0b15', color: '#f59e0b', label: 'Zaplanowany' };
  return (
    <span data-testid="post-status-badge" style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10, background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </span>
  );
};

export default function SocialSchedulePage() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ platform: 'linkedin', text: '', scheduled_at: '', hashtags: '' });
  const [submitting, setSubmitting] = useState(false);

  const fetchPosts = async () => {
    try {
      const { data } = await axios.get(`${API}/api/social/scheduled`);
      setPosts(data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchPosts(); }, []);

  const schedule = async () => {
    if (!form.text.trim() || !form.scheduled_at) {
      toast.error('Wypełnij treść i datę publikacji');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        platform: form.platform,
        text: form.text,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        hashtags: form.hashtags.split(/[,\s]+/).filter(Boolean),
      };
      await axios.post(`${API}/api/social/schedule`, payload);
      toast.success('Post zaplanowany!');
      setShowForm(false);
      setForm({ platform: 'linkedin', text: '', scheduled_at: '', hashtags: '' });
      fetchPosts();
    } catch (e) {
      toast.error('Błąd planowania postu');
    }
    setSubmitting(false);
  };

  const deletePost = async (id) => {
    try {
      await axios.delete(`${API}/api/social/scheduled/${id}`);
      toast.success('Post usunięty');
      setPosts(posts.filter(p => p.id !== id));
    } catch (e) { toast.error('Błąd usuwania'); }
  };

  const markPublished = async (id) => {
    try {
      await axios.put(`${API}/api/social/scheduled/${id}/publish`);
      toast.success('Oznaczono jako opublikowany');
      fetchPosts();
    } catch (e) { toast.error('Błąd'); }
  };

  const copyText = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Skopiowano do schowka');
    } catch { }
  };

  const scheduled = posts.filter(p => p.status === 'scheduled');
  const published = posts.filter(p => p.status === 'published');

  return (
    <div data-testid="social-schedule-page" style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>Social Media</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Planuj i zarządzaj postami na platformach społecznościowych</p>
        </div>
        <Button data-testid="new-post-btn" onClick={() => setShowForm(!showForm)} className="gap-2">
          <Plus size={16} /> Nowy post
        </Button>
      </div>

      {showForm && (
        <div data-testid="schedule-form" style={{
          padding: 20, borderRadius: 12, border: '1px solid var(--border, hsl(215,16%,90%))',
          background: 'var(--bg-card, #fff)', marginBottom: 24
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, display: 'block' }}>Platforma</label>
              <select
                data-testid="platform-select"
                value={form.platform}
                onChange={e => setForm({ ...form, platform: e.target.value })}
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 8, fontSize: 14,
                  border: '1px solid var(--border, hsl(215,16%,85%))',
                  background: 'var(--bg-card, #fff)', color: 'var(--text-primary)',
                }}
              >
                {Object.entries(PLATFORMS).map(([k, v]) => (
                  <option key={k} value={k}>{v.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, display: 'block' }}>Data publikacji</label>
              <input
                data-testid="schedule-date"
                type="datetime-local"
                value={form.scheduled_at}
                onChange={e => setForm({ ...form, scheduled_at: e.target.value })}
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 8, fontSize: 14,
                  border: '1px solid var(--border, hsl(215,16%,85%))',
                  background: 'var(--bg-card, #fff)', color: 'var(--text-primary)',
                }}
              />
            </div>
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, display: 'block' }}>Treść postu</label>
            <textarea
              data-testid="post-text"
              value={form.text}
              onChange={e => setForm({ ...form, text: e.target.value })}
              placeholder="Wpisz treść postu..."
              rows={4}
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 8, fontSize: 14,
                border: '1px solid var(--border, hsl(215,16%,85%))', resize: 'vertical',
                background: 'var(--bg-card, #fff)', color: 'var(--text-primary)',
              }}
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, display: 'block' }}>Hashtagi (oddzielone przecinkami)</label>
            <input
              data-testid="post-hashtags"
              value={form.hashtags}
              onChange={e => setForm({ ...form, hashtags: e.target.value })}
              placeholder="#księgowość, #podatki, #SEO"
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 8, fontSize: 14,
                border: '1px solid var(--border, hsl(215,16%,85%))',
                background: 'var(--bg-card, #fff)', color: 'var(--text-primary)',
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <Button data-testid="schedule-submit-btn" onClick={schedule} disabled={submitting} className="gap-2">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : <CalendarIcon size={14} />}
              Zaplanuj
            </Button>
            <Button variant="outline" onClick={() => setShowForm(false)}>Anuluj</Button>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 48 }}>
          <Loader2 size={24} className="animate-spin" style={{ color: 'var(--accent)', margin: '0 auto' }} />
        </div>
      ) : (
        <>
          {scheduled.length > 0 && (
            <div style={{ marginBottom: 32 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={18} style={{ color: '#f59e0b' }} /> Zaplanowane ({scheduled.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {scheduled.map(post => {
                  const P = PLATFORMS[post.platform] || PLATFORMS.linkedin;
                  return (
                    <div key={post.id} data-testid="scheduled-post-card" style={{
                      padding: 16, borderRadius: 12,
                      border: '1px solid var(--border, hsl(215,16%,90%))',
                      background: 'var(--bg-card, #fff)',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <P.icon size={16} style={{ color: P.color }} />
                          <span style={{ fontSize: 13, fontWeight: 600 }}>{P.label}</span>
                          <StatusBadge status={post.status} />
                        </div>
                        <div style={{ display: 'flex', gap: 4 }}>
                          <Button size="sm" variant="ghost" onClick={() => copyText(post.text)} title="Kopiuj">
                            <Copy size={14} />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => markPublished(post.id)} title="Oznacz jako opublikowany" style={{ color: '#22c55e' }}>
                            <CheckCircle size={14} />
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => deletePost(post.id)} title="Usuń" style={{ color: '#ef4444' }}>
                            <Trash2 size={14} />
                          </Button>
                        </div>
                      </div>
                      <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-primary)', marginBottom: 6 }}>{post.text}</p>
                      {post.hashtags?.length > 0 && (
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 6 }}>
                          {post.hashtags.map((h, i) => (
                            <span key={i} style={{ fontSize: 11, padding: '2px 6px', borderRadius: 8, background: 'var(--bg-muted, hsl(215,16%,94%))', color: 'var(--accent)' }}>{h}</span>
                          ))}
                        </div>
                      )}
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                        <CalendarIcon size={11} style={{ display: 'inline', verticalAlign: -1, marginRight: 4 }} />
                        {new Date(post.scheduled_at).toLocaleString('pl-PL')}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {published.length > 0 && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle size={18} style={{ color: '#22c55e' }} /> Opublikowane ({published.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {published.map(post => {
                  const P = PLATFORMS[post.platform] || PLATFORMS.linkedin;
                  return (
                    <div key={post.id} data-testid="published-post-card" style={{
                      padding: 14, borderRadius: 12,
                      border: '1px solid var(--border, hsl(215,16%,92%))',
                      background: 'var(--bg-card, #fff)', opacity: 0.85,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <P.icon size={14} style={{ color: P.color }} />
                          <span style={{ fontSize: 12, fontWeight: 600 }}>{P.label}</span>
                          <StatusBadge status={post.status} />
                        </div>
                        <Button size="sm" variant="ghost" onClick={() => deletePost(post.id)} style={{ color: '#ef4444' }}>
                          <Trash2 size={13} />
                        </Button>
                      </div>
                      <p style={{ fontSize: 12, lineHeight: 1.5, color: 'var(--text-secondary)' }}>{post.text}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {posts.length === 0 && !showForm && (
            <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-secondary)' }}>
              <CalendarIcon size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
              <p style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Brak zaplanowanych postów</p>
              <p style={{ fontSize: 13 }}>Kliknij "Nowy post" lub użyj generatora Social Media w edytorze artykułu</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
