import React, { useState, useEffect } from 'react';
import { Check, Loader2, Crown, Zap, Star, ArrowRight, Shield, Clock, CreditCard } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PLAN_ICONS = {
  monthly: Zap,
  semiannual: Star,
  annual: Crown
};

const PLAN_COLORS = {
  monthly: { bg: 'hsl(220, 95%, 96%)', border: '#04389E', accent: '#04389E' },
  semiannual: { bg: 'hsl(34, 90%, 95%)', border: '#F28C28', accent: '#F28C28' },
  annual: { bg: 'hsl(267, 60%, 96%)', border: 'hsl(267, 60%, 45%)', accent: 'hsl(267, 60%, 45%)' }
};

export default function PricingPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [subscription, setSubscription] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [plansRes, subRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/subscription/plans`),
        axios.get(`${BACKEND_URL}/api/subscription/status`).catch(() => ({ data: null }))
      ]);
      setPlans(plansRes.data);
      if (subRes.data) setSubscription(subRes.data);
    } catch (err) {
      toast.error('Blad ladowania planow');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckout = async (planId) => {
    setCheckoutLoading(planId);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/subscription/checkout`, { plan_id: planId });
      if (res.data.transaction_url) {
        window.location.href = res.data.transaction_url;
      } else {
        toast.success('Subskrypcja utworzona');
        loadData();
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad platnosci';
      toast.error(msg);
    } finally {
      setCheckoutLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="page-container" data-testid="pricing-page">
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Loader2 size={32} className="animate-spin" style={{ color: '#04389E', margin: '0 auto' }} />
        </div>
      </div>
    );
  }

  const allFeatures = [
    "Nielimitowane generowanie artykulow",
    "Generator obrazow AI (Gemini)",
    "Asystent SEO z chatbotem",
    "Edytor wizualny WYSIWYG",
    "Eksport HTML / PDF",
    "Integracja WordPress",
    "Biblioteka obrazow z tagami",
    "Serie artykulow",
    "Szablony tresci (listicle, case study)",
    "Generowanie 4 wariantow obrazow",
    "AI edycja obrazow",
    "Panel administracyjny"
  ];

  return (
    <div className="page-container" data-testid="pricing-page">
      {/* Header */}
      <div style={{ textAlign: 'center', maxWidth: 600, margin: '0 auto 40px' }}>
        <h1 style={{
          fontFamily: "'Instrument Serif', Georgia, serif",
          fontSize: 36,
          color: 'hsl(222, 47%, 11%)',
          marginBottom: 12
        }}>
          Wybierz plan<span style={{ color: '#F28C28' }}>.</span>
        </h1>
        <p style={{ fontSize: 16, color: 'hsl(215, 16%, 45%)', lineHeight: 1.6 }}>
          Pelny dostep do platformy SEO Article Builder. Generuj artykuly, obrazy i publikuj na WordPress.
        </p>
      </div>

      {/* Active subscription banner */}
      {subscription?.has_subscription && (
        <div style={{
          background: 'hsl(142, 50%, 96%)',
          border: '1px solid hsl(142, 50%, 80%)',
          borderRadius: 12,
          padding: '16px 20px',
          marginBottom: 28,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          maxWidth: 700,
          margin: '0 auto 28px'
        }} data-testid="active-subscription-banner">
          <Shield size={20} style={{ color: 'hsl(142, 71%, 35%)', flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 600, color: 'hsl(142, 71%, 25%)', fontSize: 14 }}>
              Aktywna subskrypcja: {subscription.plan_name}
            </div>
            {subscription.expires_at && (
              <div style={{ fontSize: 12, color: 'hsl(142, 40%, 40%)' }}>
                <Clock size={11} style={{ display: 'inline', marginRight: 4 }} />
                Wazna do: {new Date(subscription.expires_at).toLocaleDateString('pl-PL')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Plans grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 20,
        maxWidth: 960,
        margin: '0 auto'
      }}>
        {plans.map((plan) => {
          const PlanIcon = PLAN_ICONS[plan.id] || Zap;
          const colors = PLAN_COLORS[plan.id] || PLAN_COLORS.monthly;
          const isPopular = plan.id === 'annual';
          const isActive = subscription?.plan === plan.id && subscription?.has_subscription;

          return (
            <div
              key={plan.id}
              style={{
                background: 'white',
                borderRadius: 16,
                border: isPopular ? `2px solid ${colors.accent}` : '1px solid hsl(214, 18%, 88%)',
                padding: 28,
                position: 'relative',
                transition: 'box-shadow 0.2s, transform 0.2s',
                display: 'flex',
                flexDirection: 'column'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = `0 12px 40px rgba(15,23,42,0.10)`;
                e.currentTarget.style.transform = 'translateY(-4px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'none';
                e.currentTarget.style.transform = 'none';
              }}
              data-testid={`plan-card-${plan.id}`}
            >
              {/* Popular badge */}
              {isPopular && (
                <div style={{
                  position: 'absolute',
                  top: -12,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: colors.accent,
                  color: 'white',
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '4px 16px',
                  borderRadius: 20,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  Najpopularniejszy
                </div>
              )}

              {/* Discount badge */}
              {plan.discount_pct > 0 && (
                <Badge style={{
                  background: colors.bg,
                  color: colors.accent,
                  border: 'none',
                  fontSize: 11,
                  fontWeight: 700,
                  alignSelf: 'flex-start',
                  marginBottom: 12
                }}>
                  -{plan.discount_pct}% rabatu
                </Badge>
              )}

              {/* Icon + name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <div style={{
                  width: 42,
                  height: 42,
                  borderRadius: 12,
                  background: colors.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: colors.accent
                }}>
                  <PlanIcon size={22} />
                </div>
                <div>
                  <div style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 20, color: 'hsl(222, 47%, 11%)' }}>
                    {plan.name}
                  </div>
                  <div style={{ fontSize: 12, color: 'hsl(215, 16%, 50%)' }}>
                    {plan.period_months} {plan.period_months === 1 ? 'miesiac' : plan.period_months < 5 ? 'miesiace' : 'miesiecy'}
                  </div>
                </div>
              </div>

              {/* Price */}
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                  <span style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 36, fontWeight: 400, color: 'hsl(222, 47%, 11%)' }}>
                    {plan.price_netto.toFixed(2)}
                  </span>
                  <span style={{ fontSize: 14, color: 'hsl(215, 16%, 50%)' }}>PLN netto</span>
                </div>
                <div style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)' }}>
                  {plan.price_brutto.toFixed(2)} PLN brutto (z VAT 23%)
                </div>
                {plan.monthly_equivalent && (
                  <div style={{ fontSize: 12, color: colors.accent, fontWeight: 600, marginTop: 2 }}>
                    = {plan.monthly_equivalent.toFixed(2)} PLN / mies.
                  </div>
                )}
              </div>

              {/* CTA */}
              <Button
                onClick={() => handleCheckout(plan.id)}
                disabled={checkoutLoading === plan.id || isActive}
                className="gap-1 w-full"
                style={{
                  background: isActive ? 'hsl(142, 50%, 92%)' : (isPopular ? colors.accent : '#04389E'),
                  color: isActive ? 'hsl(142, 71%, 30%)' : 'white',
                  marginBottom: 20,
                  height: 44,
                  fontSize: 14,
                  fontWeight: 600
                }}
                data-testid={`plan-checkout-${plan.id}`}
              >
                {checkoutLoading === plan.id ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : isActive ? (
                  <><Check size={16} /> Aktywny</>
                ) : (
                  <><CreditCard size={16} /> Wykup plan</>
                )}
              </Button>

              {/* Features */}
              <div style={{ flex: 1 }}>
                {(plan.features || []).map((f, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 8,
                    marginBottom: 8,
                    fontSize: 13,
                    color: 'hsl(215, 16%, 35%)'
                  }}>
                    <Check size={15} style={{ color: colors.accent, marginTop: 2, flexShrink: 0 }} />
                    {f}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* All features section */}
      <div style={{
        maxWidth: 700,
        margin: '48px auto 0',
        background: 'white',
        borderRadius: 16,
        border: '1px solid hsl(214, 18%, 88%)',
        padding: 28
      }}>
        <h2 style={{
          fontFamily: "'Instrument Serif', Georgia, serif",
          fontSize: 22,
          color: 'hsl(222, 47%, 11%)',
          marginBottom: 20,
          textAlign: 'center'
        }}>
          Wszystkie funkcje w kazdym planie
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 10
        }}>
          {allFeatures.map((f, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              color: 'hsl(215, 16%, 35%)'
            }}>
              <Check size={14} style={{ color: '#04389E', flexShrink: 0 }} />
              {f}
            </div>
          ))}
        </div>
      </div>

      {/* Payment info */}
      <div style={{
        maxWidth: 700,
        margin: '24px auto 0',
        textAlign: 'center',
        fontSize: 12,
        color: 'hsl(215, 16%, 55%)',
        lineHeight: 1.6
      }}>
        <p>Platnosci obslugiwane przez <strong>tpay.com</strong> — bezpieczne przelewy online.</p>
        <p>Faktura VAT wystawiana automatycznie po platnosci. Subskrypcja odnawiana recznie.</p>
      </div>
    </div>
  );
}
