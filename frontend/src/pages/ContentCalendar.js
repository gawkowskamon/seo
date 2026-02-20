import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Loader2, RefreshCw, ChevronRight, Clock, Tag, Target, Sparkles, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PRIORITY_COLORS = {
  wysoki: { bg: 'hsl(0, 72%, 95%)', color: 'hsl(0, 72%, 40%)', border: 'hsl(0, 72%, 85%)' },
  sredni: { bg: 'hsl(38, 92%, 95%)', color: 'hsl(38, 70%, 35%)', border: 'hsl(38, 80%, 80%)' },
  niski: { bg: 'hsl(210, 40%, 96%)', color: 'hsl(210, 40%, 40%)', border: 'hsl(210, 30%, 85%)' }
};

const CATEGORY_LABELS = {
  vat: 'VAT', pit: 'PIT', cit: 'CIT', zus: 'ZUS',
  kadry: 'Kadry', ksiegowosc: 'Ksiegowosc', inne: 'Inne'
};

export default function ContentCalendar() {
  const navigate = useNavigate();
  const [calendar, setCalendar] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [period, setPeriod] = useState('miesiac');

  useEffect(() => { loadLatest(); }, []);

  const loadLatest = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/content-calendar/latest`);
      if (res.data) setCalendar(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/content-calendar/generate`, { period });
      setCalendar(res.data);
      toast.success('Kalendarz tresci wygenerowany');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Blad generowania kalendarza');
    } finally {
      setGenerating(false);
    }
  };

  const handleCreateArticle = (item) => {
    navigate('/generator', { state: {
      topic: item.title,
      primaryKeyword: item.primary_keyword,
      secondaryKeywords: item.secondary_keywords || []
    }});
  };

  const groupByMonth = (items) => {
    const groups = {};
    for (const item of (items || [])) {
      const key = item.month || 'inne';
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    }
    return groups;
  };

  if (loading) {
    return (
      <div className="page-container" data-testid="content-calendar-page">
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Loader2 size={32} className="animate-spin" style={{ color: '#04389E' }} />
        </div>
      </div>
    );
  }

  const monthGroups = calendar?.plan ? groupByMonth(calendar.plan.items) : {};

  return (
    <div className="page-container" data-testid="content-calendar-page">
      <div className="page-header">
        <div>
          <h1>Kalendarz tresci</h1>
          <p style={{ fontSize: 14, color: 'hsl(215, 16%, 45%)', marginTop: 4 }}>
            Plan publikacji dopasowany do sezonu podatkowego
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            data-testid="calendar-period-select"
            style={{
              padding: '8px 12px', borderRadius: 8, fontSize: 14,
              border: '1px solid hsl(214, 18%, 85%)', background: 'white'
            }}
          >
            <option value="miesiac">Miesiac</option>
            <option value="kwartal">Kwartal</option>
            <option value="polrocze">Polrocze</option>
          </select>
          <Button
            onClick={handleGenerate}
            disabled={generating}
            className="gap-2"
            data-testid="calendar-generate-btn"
          >
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {generating ? 'Generowanie...' : 'Generuj plan'}
          </Button>
        </div>
      </div>

      {!calendar ? (
        <div style={{
          textAlign: 'center', padding: '60px 20px',
          background: 'white', borderRadius: 16,
          border: '1px solid hsl(214, 18%, 88%)'
        }}>
          <Calendar size={48} style={{ color: 'hsl(215, 16%, 70%)', margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: 18, color: 'hsl(222, 47%, 11%)', marginBottom: 8 }}>
            Brak kalendarza tresci
          </h3>
          <p style={{ color: 'hsl(215, 16%, 45%)', marginBottom: 20, maxWidth: 400, margin: '0 auto 20px' }}>
            Wygeneruj plan publikacji oparty na AI, dopasowany do polskiego sezonu podatkowego.
          </p>
          <Button onClick={handleGenerate} disabled={generating} className="gap-2">
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            Generuj pierwszy plan
          </Button>
        </div>
      ) : (
        <div>
          {calendar.plan?.plan_title && (
            <div style={{
              background: 'hsl(220, 95%, 96%)', borderRadius: 12, padding: '14px 20px',
              marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10,
              border: '1px solid hsl(220, 70%, 90%)'
            }}>
              <Calendar size={18} style={{ color: '#04389E' }} />
              <span style={{ fontWeight: 600, color: '#04389E', fontSize: 15 }}>
                {calendar.plan.plan_title}
              </span>
              <span style={{ marginLeft: 'auto', fontSize: 12, color: 'hsl(215, 16%, 50%)' }}>
                Wygenerowano: {calendar.created_at ? new Date(calendar.created_at).toLocaleDateString('pl-PL') : ''}
              </span>
            </div>
          )}

          {Object.entries(monthGroups).map(([month, items]) => (
            <div key={month} style={{ marginBottom: 28 }}>
              <h2 style={{
                fontFamily: "'Instrument Serif', Georgia, serif",
                fontSize: 20, color: 'hsl(222, 47%, 11%)',
                marginBottom: 12, textTransform: 'capitalize'
              }}>
                {month}
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {items.map((item, idx) => {
                  const prioStyle = PRIORITY_COLORS[item.priority] || PRIORITY_COLORS.sredni;
                  return (
                    <div key={idx} style={{
                      background: 'white', borderRadius: 12, padding: '16px 20px',
                      border: '1px solid hsl(214, 18%, 88%)',
                      display: 'flex', alignItems: 'flex-start', gap: 16,
                      transition: 'box-shadow 0.15s',
                      cursor: 'pointer'
                    }}
                    onClick={() => handleCreateArticle(item)}
                    onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.06)'}
                    onMouseLeave={(e) => e.currentTarget.style.boxShadow = 'none'}
                    data-testid={`calendar-item-${idx}`}
                    >
                      <div style={{
                        width: 42, minHeight: 42, borderRadius: 10,
                        background: 'hsl(220, 95%, 96%)', display: 'flex',
                        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        fontSize: 11, fontWeight: 700, color: '#04389E', flexShrink: 0
                      }}>
                        <span style={{ fontSize: 14 }}>T{item.week || idx + 1}</span>
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600, fontSize: 14, color: 'hsl(222, 47%, 11%)', marginBottom: 4 }}>
                          {item.title}
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 6 }}>
                          <span style={{
                            fontSize: 11, padding: '2px 8px', borderRadius: 6,
                            background: prioStyle.bg, color: prioStyle.color,
                            border: `1px solid ${prioStyle.border}`, fontWeight: 600
                          }}>
                            {item.priority}
                          </span>
                          {item.category && (
                            <span style={{
                              fontSize: 11, padding: '2px 8px', borderRadius: 6,
                              background: 'hsl(210, 33%, 96%)', color: 'hsl(210, 30%, 40%)',
                              fontWeight: 500
                            }}>
                              {CATEGORY_LABELS[item.category] || item.category}
                            </span>
                          )}
                          {item.suggested_date && (
                            <span style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', display: 'flex', alignItems: 'center', gap: 3 }}>
                              <Clock size={10} /> {item.suggested_date}
                            </span>
                          )}
                        </div>
                        {item.reason && (
                          <p style={{ fontSize: 12, color: 'hsl(215, 16%, 45%)', margin: 0, lineHeight: 1.4 }}>
                            {item.reason}
                          </p>
                        )}
                        {item.primary_keyword && (
                          <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Target size={11} style={{ color: '#04389E' }} />
                            <span style={{ fontSize: 11, color: '#04389E', fontWeight: 500 }}>
                              {item.primary_keyword}
                            </span>
                          </div>
                        )}
                      </div>
                      <Button variant="outline" size="sm" className="gap-1" style={{ flexShrink: 0, marginTop: 4 }}
                        onClick={(e) => { e.stopPropagation(); handleCreateArticle(item); }}>
                        <FileText size={13} />
                        Napisz
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
