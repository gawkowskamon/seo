import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Image as ImageIcon, Loader2, Download, Copy, Trash2, RefreshCw, Sparkles, Camera, PenTool, BarChart3, Circle, GitBranch, TrendingUp, Edit, Palette, Layout, Zap, Minimize2, Paperclip, X, FileImage } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const STYLE_ICONS = {
  'image': ImageIcon,
  'camera': Camera,
  'pen-tool': PenTool,
  'bar-chart-3': BarChart3,
  'circle': Circle,
  'git-branch': GitBranch,
  'trending-up': TrendingUp,
  'edit': Edit,
};

const VARIATION_TYPES = [
  { id: 'color', label: 'Kolory', icon: Palette, desc: 'Inna paleta kolorow' },
  { id: 'composition', label: 'Kompozycja', icon: Layout, desc: 'Inny uklad elementow' },
  { id: 'mood', label: 'Nastroj', icon: Zap, desc: 'Inna energia i ton' },
  { id: 'simplify', label: 'Uproszczona', icon: Minimize2, desc: 'Prostsza wersja' },
];

const ImageGenerator = ({ articleId, article, onInsertImage }) => {
  const [prompt, setPrompt] = useState('');
  const [styles, setStyles] = useState([]);
  const [selectedStyle, setSelectedStyle] = useState('hero');
  const [generating, setGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [gallery, setGallery] = useState([]);
  const [loadingGallery, setLoadingGallery] = useState(true);
  const [showVariants, setShowVariants] = useState(false);
  const [generatingVariant, setGeneratingVariant] = useState(null);

  useEffect(() => {
    const fetchStyles = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/api/image-styles`);
        setStyles(res.data);
      } catch (err) {
        // Use defaults
        setStyles([
          { id: 'hero', name: 'Okladka artykulu', icon: 'image' },
          { id: 'fotorealizm', name: 'Foto-realizm', icon: 'camera' },
          { id: 'ilustracja', name: 'Ilustracja flat', icon: 'pen-tool' },
          { id: 'infografika', name: 'Infografika', icon: 'bar-chart-3' },
          { id: 'custom', name: 'Wlasny prompt', icon: 'edit' },
        ]);
      }
    };
    fetchStyles();
  }, []);

  const loadGallery = useCallback(async () => {
    if (!articleId) return;
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/${articleId}/images`);
      setGallery(res.data);
    } catch (err) {
      console.warn('Error loading gallery:', err);
    } finally {
      setLoadingGallery(false);
    }
  }, [articleId]);

  useEffect(() => {
    loadGallery();
  }, [loadGallery]);

  // Auto-fill prompt from article context
  useEffect(() => {
    if (article && !prompt) {
      const topic = article.topic || article.primary_keyword || '';
      if (topic) {
        setPrompt(topic);
      }
    }
  }, [article]);

  const handleGenerate = async (variationType = null) => {
    if (!prompt.trim()) {
      toast.error('Wpisz temat lub opis obrazu');
      return;
    }

    if (variationType) {
      setGeneratingVariant(variationType);
    } else {
      setGenerating(true);
    }

    try {
      const payload = {
        prompt: prompt.trim(),
        style: selectedStyle,
        article_id: articleId
      };
      if (variationType) {
        payload.variation_type = variationType;
      }

      const res = await axios.post(`${BACKEND_URL}/api/images/generate`, payload, { timeout: 120000 });
      
      setGeneratedImage(res.data);
      setShowVariants(true);
      await loadGallery();
      toast.success(variationType ? 'Wariant wygenerowany' : 'Obraz wygenerowany');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad generowania obrazu';
      toast.error(msg);
    } finally {
      setGenerating(false);
      setGeneratingVariant(null);
    }
  };

  const handleDelete = async (imageId) => {
    try {
      await axios.delete(`${BACKEND_URL}/api/images/${imageId}`);
      setGallery(prev => prev.filter(img => img.id !== imageId));
      if (generatedImage?.id === imageId) setGeneratedImage(null);
      toast.success('Obraz usuniety');
    } catch (err) {
      toast.error('Blad usuwania');
    }
  };

  const handleCopyHtml = (image) => {
    const html = `<img src="data:${image.mime_type};base64,${image.data}" alt="${image.prompt || ''}" style="max-width: 100%; height: auto;" />`;
    navigator.clipboard.writeText(html);
    toast.success('HTML skopiowany do schowka');
  };

  return (
    <div data-testid="image-generator-panel" style={{ padding: '16px 0' }}>
      {/* Style selector */}
      <div className="panel-section" style={{ paddingTop: 0 }}>
        <div className="panel-section-title">Styl obrazu</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
          {styles.map(style => {
            const IconComp = STYLE_ICONS[style.icon] || ImageIcon;
            const isSelected = selectedStyle === style.id;
            return (
              <button
                key={style.id}
                onClick={() => setSelectedStyle(style.id)}
                data-testid={`image-style-${style.id}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 10px',
                  borderRadius: 8,
                  border: isSelected ? '2px solid #04389E' : '1px solid hsl(214, 18%, 88%)',
                  background: isSelected ? 'hsl(220, 95%, 98%)' : 'white',
                  cursor: 'pointer',
                  fontSize: 12,
                  fontWeight: isSelected ? 600 : 500,
                  color: isSelected ? '#04389E' : 'hsl(215, 16%, 45%)',
                  transition: 'all 0.15s',
                  textAlign: 'left'
                }}
              >
                <IconComp size={14} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{style.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Prompt input */}
      <div className="panel-section">
        <div className="panel-section-title">Opis obrazu</div>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Opisz obraz lub wpisz temat artykulu..."
          data-testid="image-prompt-input"
          rows={3}
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: 8,
            border: '1px solid hsl(214, 18%, 88%)',
            fontSize: 13,
            resize: 'vertical',
            fontFamily: 'inherit',
            lineHeight: 1.4,
            outline: 'none'
          }}
        />
        <Button
          onClick={() => handleGenerate()}
          disabled={generating || !prompt.trim()}
          size="sm"
          className="gap-1 w-full mt-2"
          data-testid="image-generate-button"
        >
          {generating ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              Generowanie...
            </>
          ) : (
            <>
              <Sparkles size={14} />
              Generuj obraz
            </>
          )}
        </Button>
      </div>

      {/* Generated image preview */}
      {generatedImage && (
        <div className="panel-section">
          <div className="panel-section-title">Wygenerowany obraz</div>
          <div style={{
            borderRadius: 10,
            overflow: 'hidden',
            border: '1px solid hsl(214, 18%, 88%)',
            marginBottom: 10
          }}>
            <img
              src={`data:${generatedImage.mime_type};base64,${generatedImage.data}`}
              alt={generatedImage.prompt}
              style={{ width: '100%', display: 'block' }}
              data-testid="generated-image-preview"
            />
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {onInsertImage && (
              <Button
                size="sm"
                onClick={() => {
                  const imgHtml = `<img src="data:${generatedImage.mime_type};base64,${generatedImage.data}" alt="${generatedImage.prompt || ''}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0;" />`;
                  onInsertImage(imgHtml);
                  toast.success('Obraz wstawiony do edytora');
                }}
                className="gap-1 flex-1"
                style={{ fontSize: 11 }}
                data-testid="image-insert-editor-button"
              >
                <ImageIcon size={12} />
                Wstaw w tresc
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleCopyHtml(generatedImage)}
              className="gap-1 flex-1"
              style={{ fontSize: 11 }}
              data-testid="image-copy-html-button"
            >
              <Copy size={12} />
              Kopiuj HTML
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleGenerate()}
              disabled={generating}
              className="gap-1 flex-1"
              style={{ fontSize: 11 }}
            >
              <RefreshCw size={12} />
              Regeneruj
            </Button>
          </div>

          {/* Variant generation */}
          {showVariants && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'hsl(215, 16%, 50%)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Warianty
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
                {VARIATION_TYPES.map(v => {
                  const VIcon = v.icon;
                  const isLoading = generatingVariant === v.id;
                  return (
                    <button
                      key={v.id}
                      onClick={() => handleGenerate(v.id)}
                      disabled={generating || !!generatingVariant}
                      data-testid={`image-variant-${v.id}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '7px 10px',
                        borderRadius: 8,
                        border: '1px solid hsl(214, 18%, 88%)',
                        background: 'white',
                        cursor: generating || generatingVariant ? 'not-allowed' : 'pointer',
                        fontSize: 11,
                        fontWeight: 500,
                        color: 'hsl(215, 16%, 45%)',
                        transition: 'all 0.15s',
                        opacity: generating || generatingVariant ? 0.6 : 1
                      }}
                    >
                      {isLoading ? <Loader2 size={12} className="animate-spin" /> : <VIcon size={12} />}
                      {v.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Gallery */}
      <div className="panel-section" style={{ borderBottom: 'none' }}>
        <div className="panel-section-title">Galeria ({gallery.length})</div>
        {loadingGallery ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Loader2 size={20} className="animate-spin" style={{ color: 'hsl(215, 16%, 65%)' }} />
          </div>
        ) : gallery.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <ImageIcon size={24} style={{ color: 'hsl(215, 16%, 75%)', margin: '0 auto 8px', display: 'block' }} />
            <p style={{ fontSize: 12, color: 'hsl(215, 16%, 55%)' }}>Brak obrazow</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {gallery.map(img => (
              <div
                key={img.id}
                style={{
                  borderRadius: 8,
                  overflow: 'hidden',
                  border: '1px solid hsl(214, 18%, 88%)',
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.15s'
                }}
                data-testid="gallery-image-item"
                onClick={async () => {
                  // Load full image
                  try {
                    const res = await axios.get(`${BACKEND_URL}/api/images/${img.id}`);
                    setGeneratedImage(res.data);
                    setShowVariants(true);
                  } catch (err) {
                    toast.error('Blad ladowania obrazu');
                  }
                }}
              >
                {img.data ? (
                  <img
                    src={`data:${img.mime_type};base64,${img.data}`}
                    alt={img.prompt}
                    style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', display: 'block' }}
                  />
                ) : (
                  <div style={{
                    width: '100%', aspectRatio: '1',
                    background: 'hsl(35, 35%, 97%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <ImageIcon size={20} style={{ color: 'hsl(215, 16%, 75%)' }} />
                  </div>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(img.id); }}
                  style={{
                    position: 'absolute', top: 4, right: 4,
                    width: 24, height: 24, borderRadius: 6,
                    background: 'rgba(0,0,0,0.6)', color: 'white',
                    border: 'none', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}
                  data-testid="delete-gallery-image"
                >
                  <Trash2 size={12} />
                </button>
                <div style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0,
                  padding: '4px 6px',
                  background: 'rgba(0,0,0,0.5)',
                  color: 'white',
                  fontSize: 10
                }}>
                  {(img.style || 'custom')}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageGenerator;
