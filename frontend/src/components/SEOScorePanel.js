import React from 'react';
import { CheckCircle2, AlertCircle, XCircle, RefreshCw, Loader2, BarChart } from 'lucide-react';
import { Button } from './ui/button';

const SEOScorePanel = ({ seoScore, onRescore, scoring }) => {
  if (!seoScore) {
    return (
      <div className="panel-section" style={{ textAlign: 'center', padding: '32px 20px' }}>
        <BarChart size={40} style={{ color: 'hsl(215, 16%, 75%)', margin: '0 auto 12px' }} />
        <p style={{ fontSize: 14, color: 'hsl(215, 16%, 45%)' }}>Kliknij "Oblicz SEO" aby zobaczy\u0107 wynik</p>
        <Button variant="outline" size="sm" onClick={onRescore} disabled={scoring} className="gap-1 mt-2">
          {scoring ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Oblicz SEO
        </Button>
      </div>
    );
  }

  const percentage = seoScore.percentage || 0;
  const getScoreColor = (pct) => {
    if (pct >= 80) return 'hsl(158, 55%, 34%)';
    if (pct >= 50) return 'hsl(38, 92%, 45%)';
    return 'hsl(0, 72%, 51%)';
  };

  const getScoreLabel = (pct) => {
    if (pct >= 80) return 'Dobry';
    if (pct >= 50) return 'OK';
    return 'S\u0142aby';
  };

  const getScoreClass = (pct) => {
    if (pct >= 80) return 'high';
    if (pct >= 50) return 'medium';
    return 'low';
  };

  const scoreColor = getScoreColor(percentage);
  const circumference = 2 * Math.PI * 50;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div>
      {/* Score gauge */}
      <div className="panel-section" style={{ textAlign: 'center' }}>
        <div className="seo-score-circle" data-testid="seo-score-gauge">
          <svg width="120" height="120" viewBox="0 0 120 120" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="60" cy="60" r="50" fill="none" stroke="hsl(214, 18%, 92%)" strokeWidth="8" />
            <circle 
              cx="60" cy="60" r="50" 
              fill="none" 
              stroke={scoreColor}
              strokeWidth="8" 
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 0.8s ease' }}
            />
          </svg>
          <div className="seo-score-value" style={{ color: scoreColor }}>
            {percentage}
          </div>
        </div>
        <span className={`seo-badge ${getScoreClass(percentage)}`} style={{ fontSize: 14, padding: '4px 16px' }}>
          {getScoreLabel(percentage)}
        </span>
        <p style={{ fontSize: 12, color: 'hsl(215, 16%, 45%)', marginTop: 8 }}>
          {seoScore.word_count || 0} s\u0142\u00f3w
        </p>
      </div>

      {/* Breakdown */}
      <div className="panel-section">
        <div className="panel-section-title">Szczeg\u00f3\u0142y oceny</div>
        {seoScore.breakdown && Object.entries(seoScore.breakdown).map(([key, data]) => (
          <div key={key} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13 }}>
              <span style={{ color: 'hsl(222, 47%, 20%)' }}>{data.label}</span>
              <span style={{ fontWeight: 600, fontFamily: 'Space Grotesk, sans-serif' }}>{data.score}/{data.max}</span>
            </div>
            <div className="seo-bar">
              <div 
                className={`seo-bar-fill ${getScoreClass((data.score / data.max) * 100)}`}
                style={{ width: `${(data.score / data.max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {seoScore.recommendations && seoScore.recommendations.length > 0 && (
        <div className="panel-section" data-testid="seo-checklist">
          <div className="panel-section-title">Rekomendacje</div>
          {seoScore.recommendations.map((rec, idx) => (
            <div key={idx} className="seo-checklist-item">
              <AlertCircle size={14} className="icon" style={{ color: 'hsl(38, 92%, 45%)' }} />
              <span style={{ color: 'hsl(222, 47%, 20%)' }}>{rec}</span>
            </div>
          ))}
        </div>
      )}

      {/* Rescore button */}
      <div className="panel-section">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={onRescore}
          disabled={scoring}
          className="gap-1 w-full"
        >
          {scoring ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          Przelicz wynik SEO
        </Button>
      </div>
    </div>
  );
};

// Need to import BarChart for empty state
import { BarChart } from 'lucide-react';

export default SEOScorePanel;
