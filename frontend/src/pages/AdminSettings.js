import React, { useState, useEffect } from 'react';
import { Settings, Loader2, Check, AlertCircle, ExternalLink, Download, Globe, Key, User } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const WordPressIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h4l3 9 3-13 3 7 3-3h4" />
  </svg>
);

export default function AdminSettings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [wpUrl, setWpUrl] = useState('');
  const [wpUser, setWpUser] = useState('');
  const [wpPassword, setWpPassword] = useState('');
  const [configured, setConfigured] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/settings/wordpress`);
      if (res.data.configured) {
        setWpUrl(res.data.wp_url || '');
        setWpUser(res.data.wp_user || '');
        setConfigured(true);
      }
    } catch (err) {
      // Settings not configured yet
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    if (!wpUrl.trim() || !wpUser.trim() || !wpPassword.trim()) {
      toast.error('Wypelnij wszystkie pola');
      return;
    }
    setSaving(true);
    try {
      await axios.post(`${BACKEND_URL}/api/settings/wordpress`, {
        wp_url: wpUrl.trim(),
        wp_user: wpUser.trim(),
        wp_app_password: wpPassword.trim()
      });
      setConfigured(true);
      toast.success('Ustawienia WordPress zapisane');
    } catch (err) {
      toast.error('Blad zapisu ustawien');
    } finally {
      setSaving(false);
    }
  };

  const downloadPlugin = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/wordpress/plugin`, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'kurdynowski-importer.php';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Wtyczka pobrana');
    } catch (err) {
      toast.error('Blad pobierania wtyczki');
    }
  };

  if (loading) {
    return (
      <div className="page-container" data-testid="admin-settings-page">
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Loader2 size={32} className="animate-spin" style={{ color: '#04389E', margin: '0 auto' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="page-container" data-testid="admin-settings-page">
      <div className="page-header">
        <h1>Ustawienia</h1>
      </div>

      {/* WordPress Integration */}
      <div style={{
        background: 'white',
        borderRadius: 14,
        border: '1px solid hsl(214, 18%, 88%)',
        padding: 24,
        maxWidth: 640,
        marginBottom: 24
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: 'hsl(220, 95%, 96%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#04389E'
          }}>
            <WordPressIcon />
          </div>
          <div>
            <h2 style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 20, margin: 0, color: 'hsl(222, 47%, 11%)' }}>
              WordPress
            </h2>
            <p style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)', margin: 0 }}>
              Polacz aplikacje z WordPress aby publikowac artykuly
            </p>
          </div>
          {configured && (
            <Badge style={{ marginLeft: 'auto', background: 'hsl(142, 50%, 92%)', color: 'hsl(142, 71%, 30%)', border: 'none' }}>
              <Check size={12} style={{ marginRight: 4 }} /> Skonfigurowany
            </Badge>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <Globe size={14} /> Adres WordPress
            </label>
            <Input
              value={wpUrl}
              onChange={(e) => setWpUrl(e.target.value)}
              placeholder="https://twoja-strona.pl"
              data-testid="wp-url-input"
            />
            <p style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)', marginTop: 4 }}>
              Adres Twojej strony WordPress (bez /wp-admin)
            </p>
          </div>

          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <User size={14} /> Nazwa uzytkownika WP
            </label>
            <Input
              value={wpUser}
              onChange={(e) => setWpUser(e.target.value)}
              placeholder="admin"
              data-testid="wp-user-input"
            />
          </div>

          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <Key size={14} /> Application Password
            </label>
            <Input
              type="password"
              value={wpPassword}
              onChange={(e) => setWpPassword(e.target.value)}
              placeholder={configured ? '(zapisane - wpisz nowe aby zmienic)' : 'xxxx xxxx xxxx xxxx xxxx xxxx'}
              data-testid="wp-password-input"
            />
            <p style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)', marginTop: 4 }}>
              Wygeneruj w WordPress: Uzytkownicy &rarr; Twoj profil &rarr; Application Passwords
            </p>
          </div>

          <Button
            onClick={saveSettings}
            disabled={saving}
            className="gap-1"
            data-testid="wp-save-button"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
            Zapisz ustawienia
          </Button>
        </div>
      </div>

      {/* WordPress Plugin Download */}
      <div style={{
        background: 'white',
        borderRadius: 14,
        border: '1px solid hsl(214, 18%, 88%)',
        padding: 24,
        maxWidth: 640
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: 'hsl(34, 90%, 95%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#F28C28'
          }}>
            <Download size={20} />
          </div>
          <div>
            <h2 style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 20, margin: 0, color: 'hsl(222, 47%, 11%)' }}>
              Wtyczka WordPress
            </h2>
            <p style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)', margin: 0 }}>
              Importuj artykuly z Kurdynowski bezposrednio w panelu WordPress
            </p>
          </div>
        </div>

        <div style={{
          background: 'hsl(35, 35%, 97%)',
          borderRadius: 10,
          padding: 14,
          marginBottom: 14,
          fontSize: 12,
          color: 'hsl(215, 16%, 40%)',
          lineHeight: 1.6
        }}>
          <strong style={{ color: 'hsl(222, 47%, 11%)' }}>Jak zainstalowac:</strong>
          <ol style={{ margin: '6px 0 0', paddingLeft: 18 }}>
            <li>Pobierz plik <code style={{ background: 'hsl(214, 18%, 92%)', padding: '1px 5px', borderRadius: 3 }}>kurdynowski-importer.php</code></li>
            <li>W WordPress: Wtyczki &rarr; Dodaj nowa &rarr; Wyslij wtyczke</li>
            <li>Przeslij plik i aktywuj wtyczke</li>
            <li>Przejdz do: Kurdynowski &rarr; Ustawienia i wpisz dane logowania</li>
          </ol>
        </div>

        <Button
          variant="outline"
          onClick={downloadPlugin}
          className="gap-1 w-full"
          data-testid="wp-download-plugin-button"
        >
          <Download size={14} />
          Pobierz wtyczke (kurdynowski-importer.php)
        </Button>
      </div>
    </div>
  );
}
