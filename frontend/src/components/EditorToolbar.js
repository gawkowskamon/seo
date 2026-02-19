import React, { useCallback } from 'react';
import { Bold, Italic, Underline, Heading2, Heading3, List, ListOrdered, Link as LinkIcon, Undo, Redo, Quote, Minus, AlignLeft, AlignCenter, RemoveFormatting } from 'lucide-react';

const EditorToolbar = ({ editorRef }) => {
  const execCmd = useCallback((command, value = null) => {
    document.execCommand(command, false, value);
    if (editorRef?.current) {
      editorRef.current.focus();
    }
  }, [editorRef]);

  const insertHeading = (level) => {
    document.execCommand('formatBlock', false, `<h${level}>`);
    if (editorRef?.current) editorRef.current.focus();
  };

  const insertLink = () => {
    const url = prompt('Wpisz adres URL:');
    if (url) {
      document.execCommand('createLink', false, url);
    }
  };

  const btnStyle = {
    width: 32,
    height: 32,
    borderRadius: 6,
    border: '1px solid hsl(214, 18%, 88%)',
    background: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'hsl(215, 16%, 40%)',
    transition: 'background-color 0.12s, color 0.12s, border-color 0.12s',
    padding: 0,
    flexShrink: 0
  };

  const sepStyle = {
    width: 1,
    height: 20,
    background: 'hsl(214, 18%, 88%)',
    margin: '0 4px',
    flexShrink: 0
  };

  const handleHover = (e, enter) => {
    if (enter) {
      e.currentTarget.style.background = 'hsl(220, 95%, 96%)';
      e.currentTarget.style.color = '#04389E';
      e.currentTarget.style.borderColor = '#04389E';
    } else {
      e.currentTarget.style.background = 'white';
      e.currentTarget.style.color = 'hsl(215, 16%, 40%)';
      e.currentTarget.style.borderColor = 'hsl(214, 18%, 88%)';
    }
  };

  const ToolBtn = ({ icon: Icon, title, onClick, size = 15 }) => (
    <button
      style={btnStyle}
      title={title}
      onMouseDown={(e) => { e.preventDefault(); onClick(); }}
      onMouseEnter={(e) => handleHover(e, true)}
      onMouseLeave={(e) => handleHover(e, false)}
      data-testid={`toolbar-${title.toLowerCase().replace(/\s/g, '-')}`}
    >
      <Icon size={size} />
    </button>
  );

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 3,
      padding: '6px 16px',
      background: 'white',
      borderBottom: '1px solid hsl(214, 18%, 88%)',
      overflowX: 'auto',
      flexShrink: 0
    }} data-testid="editor-toolbar">
      <ToolBtn icon={Undo} title="Cofnij" onClick={() => execCmd('undo')} />
      <ToolBtn icon={Redo} title="Ponow" onClick={() => execCmd('redo')} />
      <div style={sepStyle} />
      <ToolBtn icon={Bold} title="Pogrubienie" onClick={() => execCmd('bold')} />
      <ToolBtn icon={Italic} title="Kursywa" onClick={() => execCmd('italic')} />
      <ToolBtn icon={Underline} title="Podkreslenie" onClick={() => execCmd('underline')} />
      <div style={sepStyle} />
      <ToolBtn icon={Heading2} title="Naglowek H2" onClick={() => insertHeading(2)} />
      <ToolBtn icon={Heading3} title="Naglowek H3" onClick={() => insertHeading(3)} />
      <div style={sepStyle} />
      <ToolBtn icon={List} title="Lista" onClick={() => execCmd('insertUnorderedList')} />
      <ToolBtn icon={ListOrdered} title="Lista numerowana" onClick={() => execCmd('insertOrderedList')} />
      <div style={sepStyle} />
      <ToolBtn icon={LinkIcon} title="Link" onClick={insertLink} />
      <ToolBtn icon={Quote} title="Cytat" onClick={() => execCmd('formatBlock', '<blockquote>')} />
      <ToolBtn icon={Minus} title="Linia" onClick={() => execCmd('insertHorizontalRule')} />
      <div style={sepStyle} />
      <ToolBtn icon={AlignLeft} title="Akapit" onClick={() => execCmd('formatBlock', '<p>')} />
      <ToolBtn icon={RemoveFormatting} title="Usun formatowanie" onClick={() => execCmd('removeFormat')} />
    </div>
  );
};

export default EditorToolbar;
