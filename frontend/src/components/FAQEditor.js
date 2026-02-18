import React from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from './ui/button';

const FAQEditor = ({ faq, onChange }) => {
  const addFAQ = () => {
    onChange([...faq, { question: '', answer: '' }]);
  };

  const removeFAQ = (index) => {
    const newFaq = faq.filter((_, i) => i !== index);
    onChange(newFaq);
  };

  const updateFAQ = (index, field, value) => {
    const newFaq = [...faq];
    newFaq[index] = { ...newFaq[index], [field]: value };
    onChange(newFaq);
  };

  return (
    <div>
      <div className="panel-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div className="panel-section-title" style={{ marginBottom: 0 }}>Pytania i odpowiedzi ({faq.length})</div>
          <Button variant="outline" size="sm" onClick={addFAQ} className="gap-1" data-testid="faq-add-button">
            <Plus size={14} /> Dodaj
          </Button>
        </div>

        {faq.length === 0 ? (
          <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', textAlign: 'center', padding: '16px 0' }}>
            Brak pyta\u0144 FAQ. Kliknij "Dodaj" aby utworzy\u0107 nowe.
          </p>
        ) : (
          faq.map((item, idx) => (
            <div key={idx} className="faq-item">
              <div className="faq-item-header">
                <span style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)' }}>Pytanie {idx + 1}</span>
                <button 
                  className="btn-icon" 
                  style={{ width: 28, height: 28 }}
                  onClick={() => removeFAQ(idx)}
                  data-testid="faq-remove-button"
                  title="Usu\u0144"
                >
                  <Trash2 size={14} />
                </button>
              </div>
              <input
                value={item.question}
                onChange={(e) => updateFAQ(idx, 'question', e.target.value)}
                placeholder="Wpisz pytanie..."
                data-testid={`faq-question-${idx}`}
              />
              <textarea
                value={item.answer}
                onChange={(e) => updateFAQ(idx, 'answer', e.target.value)}
                placeholder="Wpisz odpowied\u017a..."
                data-testid={`faq-answer-${idx}`}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default FAQEditor;
