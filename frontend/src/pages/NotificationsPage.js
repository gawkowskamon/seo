import React, { useState, useEffect } from 'react';
import { Bell, Mail, Clock, AlertTriangle, TrendingDown, FileText, Loader2, Send, CheckCircle, Settings, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;

const SeverityBadge = ({ severity }) => {
  const cfg = severity === 'critical'
    ? { bg: '#ef444415', color: '#ef4444', label: 'Krytyczny' }
    : { bg: '#f59e0b15', color: '#f59e0b', label: 'Ostrzeżenie' };
  return (
    <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10, background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </span>
  );
};

export default function NotificationsPage() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [loadingCheck, setLoadingCheck] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  const [history, setHistory] = useState([]);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [sRes, hRes] = await Promise.all([
          axios.get(`${API}/api/notifications/settings`),
          axios.get(`${API}/api/notifications/history`),
        ]);
        setSettings(sRes.data);
        setHistory(hRes.data);
      } catch (e) { console.error(e); }
      setLoadingSettings(false);
    };
    fetchAll();
  }, []);

  const checkUpdates = async () => {
    setLoadingCheck(true);
    try {
      const { data } = await axios.post(`${API}/api/notifications/check-updates`);
      setNotifications(data.notifications || []);
      if (data.total === 0) toast.success('Wszystkie artykuły są aktualne!');
      else toast.info(`Znaleziono ${data.total} powiadomień`);
    } catch (e) { toast.error('Błąd sprawdzania'); }
    setLoadingCheck(false);
  };

  const sendTest = async () => {
    setSendingTest(true);
    try {
      const { data } = await axios.post(`${API}/api/notifications/send-test`);
      toast.success(data.message);
      const hRes = await axios.get(`${API}/api/notifications/history`);
      setHistory(hRes.data);
    } catch (e) { toast.error('Błąd wysyłania'); }
    setSendingTest(false);
  };

  const updateSetting = async (key, value) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    try {
      await axios.put(`${API}/api/notifications/settings`, { [key]: value });
    } catch (e) { toast.error('Błąd zapisu ustawień'); }
  };

  const ToggleSwitch = ({ checked, onChange, testId }) => (
    <div
      data-testid={testId}
      onClick={() => onChange(!checked)}
      style={{
        width: 40, height: 22, borderRadius: 11, cursor: 'pointer',
        background: checked ? 'var(--accent, #3b82f6)' : 'var(--border, hsl(215,16%,80%))',
        position: 'relative', transition: 'background 0.2s',
      }}
    >
      <div style={{
        width: 18, height: 18, borderRadius: '50%', background: '#fff',
        position: 'absolute', top: 2, left: checked ? 20 : 2,
        transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
      }} />
    </div>
  );

  return (
    <div data-testid="notifications-page" style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 4 }}>Powiadomienia</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Monitoruj artykuły i otrzymuj alerty o potrzebnych aktualizacjach</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button data-testid="check-updates-btn" onClick={checkUpdates} disabled={loadingCheck} className="gap-2">
            {loadingCheck ? <Loader2 size={14} className="animate-spin" /> : <Bell size={14} />}
            Sprawdź aktualizacje
          </Button>
          <Button data-testid="send-test-btn" variant="outline" onClick={sendTest} disabled={sendingTest} className="gap-2">
            {sendingTest ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Wyślij test
          </Button>
        </div>
      </div>

      {/* Settings Panel */}
      <div style={{
        border: '1px solid var(--border, hsl(215,16%,90%))', borderRadius: 12,
        background: 'var(--bg-card, #fff)', marginBottom: 24, overflow: 'hidden'
      }}>
        <div
          onClick={() => setShowSettings(!showSettings)}
          style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '14px 16px', cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Settings size={16} style={{ color: 'var(--text-secondary)' }} />
            <span style={{ fontSize: 14, fontWeight: 700 }}>Ustawienia powiadomień</span>
          </div>
          {showSettings ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
        {showSettings && settings && (
          <div style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Powiadomienia email</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Otrzymuj alerty na email</div>
              </div>
              <ToggleSwitch checked={settings.email_enabled} onChange={v => updateSetting('email_enabled', v)} testId="toggle-email" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Alert: stary artykuł</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Powiadom gdy artykuł przekroczy {settings.article_age_days} dni</div>
              </div>
              <ToggleSwitch checked={settings.notify_article_age} onChange={v => updateSetting('notify_article_age', v)} testId="toggle-age" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Alert: spadek SEO</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Powiadom gdy wynik SEO spadnie poniżej 60%</div>
              </div>
              <ToggleSwitch checked={settings.notify_seo_drop} onChange={v => updateSetting('notify_seo_drop', v)} testId="toggle-seo" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Monitorowanie konkurencji</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Alerty o zmianach w SERP</div>
              </div>
              <ToggleSwitch checked={settings.notify_competition} onChange={v => updateSetting('notify_competition', v)} testId="toggle-competition" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Częstotliwość:</span>
              {['daily', 'weekly', 'monthly'].map(f => (
                <button
                  key={f}
                  data-testid={`freq-${f}`}
                  onClick={() => updateSetting('frequency', f)}
                  style={{
                    fontSize: 12, padding: '4px 12px', borderRadius: 8,
                    border: '1px solid',
                    borderColor: settings.frequency === f ? 'var(--accent, #3b82f6)' : 'var(--border)',
                    background: settings.frequency === f ? 'var(--accent, #3b82f6)' : 'transparent',
                    color: settings.frequency === f ? '#fff' : 'var(--text-secondary)',
                    cursor: 'pointer',
                  }}
                >
                  {f === 'daily' ? 'Codziennie' : f === 'weekly' ? 'Tygodniowo' : 'Miesięcznie'}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Notifications List */}
      {notifications.length > 0 && (
        <div style={{
          border: '1px solid var(--border, hsl(215,16%,90%))', borderRadius: 12,
          overflow: 'hidden', marginBottom: 24
        }}>
          <div style={{
            padding: '12px 16px', background: 'var(--bg-muted, hsl(215,16%,97%))',
            borderBottom: '1px solid var(--border)',
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 700 }}>
              <AlertTriangle size={16} style={{ display: 'inline', verticalAlign: -3, marginRight: 6, color: '#f59e0b' }} />
              Artykuły wymagające uwagi ({notifications.length})
            </h3>
          </div>
          {notifications.map((n, i) => (
            <div
              key={i}
              data-testid="notification-item"
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '12px 16px',
                borderBottom: i < notifications.length - 1 ? '1px solid var(--border, hsl(215,16%,95%))' : 'none',
                cursor: 'pointer',
              }}
              onClick={() => n.article_id && navigate(`/editor/${n.article_id}`)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {n.type === 'article_age' ? (
                  <Clock size={16} style={{ color: '#f59e0b', flexShrink: 0 }} />
                ) : (
                  <TrendingDown size={16} style={{ color: '#ef4444', flexShrink: 0 }} />
                )}
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{n.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{n.message}</div>
                </div>
              </div>
              <SeverityBadge severity={n.severity} />
            </div>
          ))}
        </div>
      )}

      {notifications.length === 0 && !loadingCheck && (
        <div style={{
          textAlign: 'center', padding: 32,
          border: '1px solid var(--border)', borderRadius: 12, marginBottom: 24,
          background: 'var(--bg-card, #fff)',
        }}>
          <CheckCircle size={32} style={{ color: '#22c55e', margin: '0 auto 8px' }} />
          <p style={{ fontSize: 14, fontWeight: 600 }}>Wszystko w porządku</p>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Kliknij "Sprawdź aktualizacje" aby zweryfikować stan artykułów</p>
        </div>
      )}

      {/* Email History */}
      {history.length > 0 && (
        <div style={{
          border: '1px solid var(--border, hsl(215,16%,90%))', borderRadius: 12,
          overflow: 'hidden'
        }}>
          <div style={{
            padding: '12px 16px', background: 'var(--bg-muted, hsl(215,16%,97%))',
            borderBottom: '1px solid var(--border)',
          }}>
            <h3 style={{ fontSize: 15, fontWeight: 700 }}>
              <Mail size={16} style={{ display: 'inline', verticalAlign: -3, marginRight: 6 }} />
              Historia wysyłek ({history.length})
            </h3>
          </div>
          {history.map((h, i) => (
            <div key={i} data-testid="email-history-item" style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 16px', fontSize: 13,
              borderBottom: i < history.length - 1 ? '1px solid var(--border, hsl(215,16%,95%))' : 'none',
            }}>
              <div>
                <span style={{ fontWeight: 500 }}>{h.subject}</span>
                <span style={{ color: 'var(--text-secondary)', marginLeft: 8, fontSize: 12 }}>do: {h.email}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  fontSize: 11, padding: '2px 8px', borderRadius: 10,
                  background: '#22c55e15', color: '#22c55e', fontWeight: 600,
                }}>
                  {h.status === 'sent_mock' ? 'MOCK' : 'Wysłano'}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                  {new Date(h.sent_at).toLocaleString('pl-PL')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
