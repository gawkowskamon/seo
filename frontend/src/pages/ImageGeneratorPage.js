import React from 'react';
import { Sparkles } from 'lucide-react';
import ImageGenerator from '../components/ImageGenerator';

export default function ImageGeneratorPage() {
  return (
    <div className="page-container" data-testid="image-generator-page">
      <div className="page-header">
        <h1>Generator obrazow</h1>
      </div>
      <div style={{
        maxWidth: 480,
        background: 'white',
        borderRadius: 14,
        border: '1px solid hsl(214, 18%, 88%)',
        padding: '4px 16px 16px',
        boxShadow: '0 1px 4px rgba(15,23,42,0.04)'
      }}>
        <ImageGenerator articleId={null} article={null} onInsertImage={null} />
      </div>
    </div>
  );
}
