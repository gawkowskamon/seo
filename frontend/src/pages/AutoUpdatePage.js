import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, Loader2, AlertTriangle, CheckCircle2, ArrowRight, Clock, Sparkles, Scale, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const URGENCY_STYLE = {
  pilny: { bg: 'hsl(0, 72%, 95%)', color: 'hsl(0, 72%, 40%)', border: 'hsl(0, 50%, 85%)', label: 'Pilny' },
  zalecany: { bg: 'hsl(38, 92%, 95%)', color: 'hsl(38, 70%, 35%)', border: 'hsl(38, 80%, 80%)', label: 'Zalecany' },
  opcjonalny: { bg: 'hsl(210, 33%, 96%)', color: 'hsl(210, 30%, 40%)', border: 'hsl(210, 30%, 85%)', label: 'Opcjonalny' }
};

const TYPE_LABELS = {
  zmiana_przepisow: 'Zmiana przepisow',
  nieaktualne_stawki: 'Nieaktualne stawki',
  nowa_regulacja: 'Nowa regulacja',
  przedawniony: 'Przedawniony',
  blad_merytoryczny: 'Blad merytoryczny'
};

export default function AutoUpdatePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCheck = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/check-updates`, {}, { timeout: 120000 });
      setResult(res.data);
      toast.success('Analiza zakonczona');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad analizy');
    } finally {
      setLoading(false);
    }
  };

  const needingUpdate = result?.articles_needing_update || [];
  const upToDate = result?.up_to_date_articles || [];
  const legalUpdates = result?.legal_updates_summary || [];

  return (
    <div className="page-container" data-testid="auto-update-page">
      <div className="page-header">
        <div>
          <h1>Aktualizacja artykulow</h1>
          <p style={{ fontSize: 14, color: 'hsl(215, 16%, 45%)', marginTop: 4 }}>
            AI sprawdzi czy artykuly wymagaja aktualizacji na podstawie zmian w przepisach
          </p>
        </div>
        <Button onClick={handleCheck} disabled={loading} className="gap-2" data-testid="check-updates-btn">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {loading ? 'Analizowanie...' : 'Sprawdz artykuly'}
        </Button>
      </div>

      {!result && !loading && (
        <div style={{
          textAlign: 'center', padding: '60px 20px',
          background: 'white', borderRadius: 16,
          border: '1px solid hsl(214, 18%, 88%)'
        }}>
          <RefreshCw size={48} style={{ color: 'hsl(215, 16%, 70%)', margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: 18, color: 'hsl(222, 47%, 11%)', marginBottom: 8 }}>
            Sprawdz aktualnosc artykulow
          </h3>
          <p style={{ color: 'hsl(215, 16%, 45%)', maxWidth: 440, margin: '0 auto 20px' }}>
            AI przeanalizuje wszystkie artykuly pod katem zmian w przepisach podatkowych, stawkach ZUS/PIT/CIT i innych regulacjach.
          </p>
          <Button onClick={handleCheck} disabled={loading} className="gap-2">
            <Sparkles size={16} />
            Rozpocznij analize
          </Button>
        </div>
      )}

      {loading && (
        <div style={{
          textAlign: 'center', padding: '60px 20px',
          background: 'white', borderRadius: 16,
          border: '1px solid hsl(214, 18%, 88%)'
        }}>
          <Loader2 size={36} className="animate-spin" style={{ color: '#04389E', margin: '0 auto 16px' }} />
          <p style={{ color: 'hsl(215, 16%, 45%)' }}>
            Analizowanie artykulow i sprawdzanie przepisow... (moze zaj 30-60 sekund)
          </p>
        </div>
      )}

      {result && (
        <div>
          {result.summary && (
            <div style={{
              background: 'hsl(220, 95%, 96%)', borderRadius: 12, padding: '14px 20px',
              marginBottom: 20, fontSize: 14, color: '#04389E', lineHeight: 1.5,
              border: '1px solid hsl(220, 70%, 90%)'
            }}>
              {result.summary}
            </div>
          )}

          {legalUpdates.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h2 style={{
                fontFamily: "'Instrument Serif', Georgia, serif",
                fontSize: 18, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8
              }}>
                <Scale size={18} style={{ color: '#04389E' }} />
                Zmiany w przepisach
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
                {legalUpdates.map((u, i) => (
                  <div key={i} style={{
                    background: 'white', borderRadius: 12, padding: 16,
                    border: '1px solid hsl(214, 18%, 88%)'
                  }}>
                    <div style={{ fontWeight: 700, fontSize: 13, color: '#04389E', marginBottom: 4 }}>{u.area}</div>
                    <div style={{ fontSize: 12, color: 'hsl(215, 16%, 40%)', marginBottom: 6, lineHeight: 1.4 }}>{u.change}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'hsl(215, 16%, 55%)' }}>
                      <span><Clock size={10} style={{ display: 'inline', marginRight: 3, verticalAlign: 'middle' }} />{u.effective_date}</span>
                      <span>{u.affected_articles_count} art.</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {needingUpdate.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <h2 style={{
                fontFamily: "'Instrument Serif', Georgia, serif",
                fontSize: 18, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8
              }}>
                <AlertTriangle size={18} style={{ color: 'hsl(38, 92%, 45%)' }} />
                Wymagaja aktualizacji ({needingUpdate.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {needingUpdate.map((art, i) => {
                  const uStyle = URGENCY_STYLE[art.urgency] || URGENCY_STYLE.zalecany;
                  return (
                    <div key={i} style={{
                      background: 'white', borderRadius: 14, padding: '18px 22px',
                      border: `1px solid ${uStyle.border}`,
                      borderLeft: `4px solid ${uStyle.color}`
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                        <span style={{
                          fontSize: 10, padding: '2px 10px', borderRadius: 6, fontWeight: 700,
                          background: uStyle.bg, color: uStyle.color, textTransform: 'uppercase'
                        }}>
                          {uStyle.label}
                        </span>
                        <h3 style={{ fontSize: 15, fontWeight: 600, flex: 1, margin: 0 }}>{art.article_title}</h3>
                        {art.article_id && (
                          <Button variant="outline" size="sm" className="gap-1"
                            onClick={() => navigate(`/editor/${art.article_id}`)}>
                            <ArrowRight size={13} /> Edytuj
                          </Button>
                        )}
                      </div>
                      {(art.reasons || []).map((r, j) => (
                        <div key={j} style={{
                          background: 'hsl(0, 0%, 98%)', borderRadius: 8, padding: '8px 12px',
                          marginBottom: 6, fontSize: 12
                        }}>
                          <span style={{
                            fontWeight: 700, color: 'hsl(215, 16%, 40%)', marginRight: 8,
                            fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em'
                          }}>
                            {TYPE_LABELS[r.type] || r.type}
                          </span>
                          <span style={{ color: 'hsl(215, 16%, 35%)' }}>{r.description}</span>
                          {r.specific_change && (
                            <div style={{ color: '#04389E', fontWeight: 600, marginTop: 4, fontSize: 11 }}>
                              {r.specific_change}
                            </div>
                          )}
                        </div>
                      ))}
                      {(art.suggested_changes || []).length > 0 && (
                        <div style={{ marginTop: 8 }}>
                          <span style={{ fontSize: 11, fontWeight: 700, color: 'hsl(215, 16%, 40%)', textTransform: 'uppercase' }}>
                            Sugerowane zmiany:
                          </span>
                          <ul style={{ margin: '4px 0 0 16px', fontSize: 12, color: 'hsl(215, 16%, 35%)' }}>
                            {art.suggested_changes.map((c, k) => <li key={k}>{c}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {upToDate.length > 0 && (
            <div>
              <h2 style={{
                fontFamily: "'Instrument Serif', Georgia, serif",
                fontSize: 18, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8
              }}>
                <CheckCircle2 size={18} style={{ color: 'hsl(142, 71%, 35%)' }} />
                Aktualne ({upToDate.length})
              </h2>
              <div style={{
                background: 'white', borderRadius: 14, padding: 16,
                border: '1px solid hsl(142, 50%, 85%)'
              }}>
                {upToDate.map((art, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 0',
                    borderBottom: i < upToDate.length - 1 ? '1px solid hsl(214, 18%, 93%)' : 'none'
                  }}>
                    <CheckCircle2 size={14} style={{ color: 'hsl(142, 71%, 45%)', flexShrink: 0 }} />
                    <span style={{ fontSize: 13, fontWeight: 500 }}>{art.article_title}</span>
                    <span style={{ fontSize: 11, color: 'hsl(215, 16%, 55%)', marginLeft: 'auto' }}>{art.note}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
