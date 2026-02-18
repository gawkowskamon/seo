import React from 'react';
import { Hash, Link as LinkIcon } from 'lucide-react';
import { toast } from 'sonner';

const TOCPanel = ({ sections, toc }) => {
  const copyAnchor = (anchor) => {
    navigator.clipboard.writeText(`#${anchor}`);
    toast.success(`Anchor #${anchor} skopiowany`);
  };

  const items = [];
  
  // Build TOC from sections
  for (const section of sections) {
    items.push({
      label: section.heading,
      anchor: section.anchor,
      level: 'h2'
    });
    for (const sub of (section.subsections || [])) {
      items.push({
        label: sub.heading,
        anchor: sub.anchor,
        level: 'h3'
      });
    }
  }

  if (items.length === 0) {
    return (
      <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', textAlign: 'center', padding: '16px 0' }}>
        Brak sekcji w artykule.
      </p>
    );
  }

  return (
    <div data-testid="toc-list">
      {items.map((item, idx) => (
        <div 
          key={idx} 
          className={`toc-item ${item.level}`}
          onClick={() => copyAnchor(item.anchor)}
          title={`Kliknij aby skopiowa\u0107 #${item.anchor}`}
        >
          {item.level === 'h2' ? (
            <Hash size={14} style={{ color: 'hsl(209, 88%, 36%)', flexShrink: 0 }} />
          ) : (
            <LinkIcon size={12} style={{ color: 'hsl(215, 16%, 65%)', flexShrink: 0 }} />
          )}
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {item.label}
          </span>
          <span 
            style={{ 
              marginLeft: 'auto', 
              fontSize: 10, 
              color: 'hsl(215, 16%, 65%)',
              fontFamily: 'IBM Plex Mono, monospace',
              flexShrink: 0
            }}
            data-testid="toc-anchor-input"
          >
            #{item.anchor}
          </span>
        </div>
      ))}
    </div>
  );
};

export default TOCPanel;
