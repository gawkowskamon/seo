import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, User, Loader2, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';

const AuthPage = () => {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Wypelnij wszystkie pola');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'login') {
        await login(email, password);
        toast.success('Zalogowano pomyslnie');
      } else {
        if (password.length < 6) {
          toast.error('Haslo musi miec minimum 6 znakow');
          setLoading(false);
          return;
        }
        await register(email, password, fullName);
        toast.success('Konto utworzone pomyslnie');
      }
      navigate('/');
    } catch (err) {
      console.error('Login/Register error:', err.response?.status, err.response?.data, err.message);
      const msg = err.response?.data?.detail || 'Wystapil blad';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'hsl(210, 33%, 99%)',
      padding: 20
    }}>
      <div style={{
        width: '100%',
        maxWidth: 420,
        background: 'white',
        borderRadius: 16,
        border: '1px solid hsl(214, 18%, 88%)',
        padding: '40px 36px',
        boxShadow: '0 8px 30px rgba(4, 56, 158, 0.06)'
      }}>
        {/* Brand header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <img 
            src="https://static.prod-images.emergentagent.com/jobs/03a9d366-f1af-4aca-be22-7750e2cedcf9/images/d0d934dc57a3eeae9c2f153104d1f3e94b5ebbbf83e571a8f1bebe771ffb8f14.png"
            alt="Kurdynowski"
            style={{ width: 56, height: 56, borderRadius: 14, marginBottom: 12, objectFit: 'contain' }}
          />
          <h1 style={{
            fontFamily: "'Instrument Serif', Georgia, serif",
            fontSize: 28, fontWeight: 400,
            color: '#04389E', margin: '0 0 2px'
          }}>
            Kurdynowski<span style={{ color: '#F28C28' }}>.</span>
          </h1>
          <p style={{
            fontSize: 11, color: '#64748B',
            textTransform: 'uppercase', letterSpacing: '0.06em',
            fontWeight: 600
          }}>
            SEO Article Builder
          </p>
        </div>

        {/* Mode toggle */}
        <div style={{
          display: 'flex', borderRadius: 10,
          border: '1px solid hsl(214, 18%, 88%)',
          marginBottom: 24, overflow: 'hidden'
        }}>
          <button
            onClick={() => setMode('login')}
            data-testid="auth-login-tab"
            style={{
              flex: 1, padding: '10px 0',
              fontSize: 14, fontWeight: 600,
              border: 'none', cursor: 'pointer',
              background: mode === 'login' ? '#04389E' : 'transparent',
              color: mode === 'login' ? 'white' : 'hsl(215, 16%, 45%)',
              transition: 'background-color 0.15s, color 0.15s'
            }}
          >
            Logowanie
          </button>
          <button
            onClick={() => setMode('register')}
            data-testid="auth-register-tab"
            style={{
              flex: 1, padding: '10px 0',
              fontSize: 14, fontWeight: 600,
              border: 'none', cursor: 'pointer',
              background: mode === 'register' ? '#04389E' : 'transparent',
              color: mode === 'register' ? 'white' : 'hsl(215, 16%, 45%)',
              transition: 'background-color 0.15s, color 0.15s'
            }}
          >
            Rejestracja
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {mode === 'register' && (
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
                Imie i nazwisko
              </label>
              <div style={{ position: 'relative' }}>
                <User size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
                <Input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jan Kowalski"
                  style={{ paddingLeft: 36 }}
                  data-testid="auth-fullname-input"
                />
              </div>
            </div>
          )}

          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
              Adres email
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@firma.pl"
                style={{ paddingLeft: 36 }}
                data-testid="auth-email-input"
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
              Haslo
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'Min. 6 znakow' : 'Twoje haslo'}
                style={{ paddingLeft: 36 }}
                data-testid="auth-password-input"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="gap-2 w-full"
            size="lg"
            style={{ marginTop: 8 }}
            data-testid="auth-submit-button"
          >
            {loading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <>
                {mode === 'login' ? 'Zaloguj sie' : 'Utworz konto'}
                <ArrowRight size={16} />
              </>
            )}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default AuthPage;
