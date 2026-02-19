import React, { useState, useEffect } from 'react';
import { Image, Loader2, Wand2, Download, Trash2, Copy, Plus, X, ImagePlus } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const STYLES = [
  { value: 'hero', label: 'Hero / Główny' },
  { value: 'section', label: 'Ilustracja sekcji' },
  { value: 'infographic', label: 'Infografika' },
  { value: 'custom', label: 'Własny prompt' },
];

const ImageGenerator = ({ articleId, articleTitle, articleTopic }) => {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('hero');
  const [generating, setGenerating] = useState(false);
  const [images, setImages] = useState([]);
  const [loadingImages, setLoadingImages] = useState(true);
  const [selectedImage, setSelectedImage] = useState(null);
  const [showGenerator, setShowGenerator] = useState(false);

  useEffect(() => {
    if (articleId) {
      fetchImages();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [articleId]);

  useEffect(() => {
    // Auto-fill prompt based on style and article info
    if (style !== 'custom') {
      setPrompt(articleTopic || articleTitle || '');
    }
  }, [style, articleTopic, articleTitle]);

  const fetchImages = async () => {
    try {
      setLoadingImages(true);
      const res = await axios.get(`${BACKEND_URL}/api/articles/${articleId}/images`);
      setImages(res.data);
    } catch (e) {
      console.error('Error fetching images:', e);
    } finally {
      setLoadingImages(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Podaj opis obrazu');
      return;
    }

    setGenerating(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/images/generate`, {
        prompt: prompt.trim(),
        style: style,
        article_id: articleId
      }, { timeout: 120000 });

      // Fetch full image with data
      const imageRes = await axios.get(`${BACKEND_URL}/api/images/${res.data.id}`);
      
      setImages(prev => [imageRes.data, ...prev]);
      setSelectedImage(imageRes.data);
      setShowGenerator(false);
      toast.success('Obraz wygenerowany!');
    } catch (e) {
      const msg = e.response?.data?.detail || 'Błąd generowania obrazu';
      toast.error(msg);
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (imageId) => {
    if (!window.confirm('Czy na pewno chcesz usunąć ten obraz?')) return;
    try {
      await axios.delete(`${BACKEND_URL}/api/images/${imageId}`);
      setImages(prev => prev.filter(img => img.id !== imageId));
      if (selectedImage?.id === imageId) setSelectedImage(null);
      toast.success('Obraz usunięty');
    } catch (e) {
      toast.error('Błąd usuwania obrazu');
    }
  };

  const handleCopyHtml = (image) => {
    const imgSrc = image.data 
      ? `data:${image.mime_type};base64,${image.data}`
      : '';
    const html = `<img src="${imgSrc}" alt="${image.prompt || 'Ilustracja artykułu'}" style="max-width:100%;height:auto;border-radius:8px;margin:16px 0;" />`;
    navigator.clipboard.writeText(html);
    toast.success('HTML obrazu skopiowany! Wklej w edytorze HTML.');
  };

  const handleDownload = (image) => {
    if (!image.data) return;
    const byteCharacters = atob(image.data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: image.mime_type || 'image/jpeg' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `article-image-${image.id?.slice(0, 8) || 'img'}.${image.mime_type?.includes('png') ? 'png' : 'jpg'}`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Obraz pobrany');
  };

  const loadFullImage = async (image) => {
    if (image.data) {
      setSelectedImage(image);
      return;
    }
    try {
      const res = await axios.get(`${BACKEND_URL}/api/images/${image.id}`);
      const fullImage = res.data;
      // Update in list
      setImages(prev => prev.map(img => img.id === fullImage.id ? fullImage : img));
      setSelectedImage(fullImage);
    } catch (e) {
      toast.error('Błąd ładowania obrazu');
    }
  };

  return (
    <div>
      {/* Image Generator Form */}
      <div className="panel-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div className="panel-section-title" style={{ marginBottom: 0 }}>
            Obrazy ({images.length})
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setShowGenerator(!showGenerator)} 
            className="gap-1"
            data-testid="image-generate-toggle"
          >
            {showGenerator ? <X size={14} /> : <ImagePlus size={14} />}
            {showGenerator ? 'Zamknij' : 'Generuj'}
          </Button>
        </div>

        {showGenerator && (
          <div style={{ 
            background: 'hsl(210, 22%, 96%)', 
            borderRadius: 10, 
            padding: 14, 
            marginBottom: 12,
            border: '1px solid hsl(214, 18%, 88%)'
          }}>
            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)', display: 'block', marginBottom: 4 }}>Styl obrazu</label>
              <Select value={style} onValueChange={setStyle}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STYLES.map(s => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'hsl(215, 16%, 45%)', display: 'block', marginBottom: 4 }}>
                {style === 'custom' ? 'Własny prompt' : 'Temat / opis'}
              </label>
              <Input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={style === 'custom' ? 'Opisz dokładnie jaki obraz chcesz...' : 'np. Rozliczanie VAT w firmie'}
                data-testid="image-prompt-input"
              />
            </div>
            <Button
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              size="sm"
              className="gap-1 w-full"
              data-testid="image-generate-button"
            >
              {generating ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Generowanie (15-30s)...
                </>
              ) : (
                <>
                  <Wand2 size={14} />
                  Generuj obraz
                </>
              )}
            </Button>
          </div>
        )}
      </div>

      {/* Selected Image Preview */}
      {selectedImage && selectedImage.data && (
        <div className="panel-section">
          <div style={{ position: 'relative' }}>
            <img
              src={`data:${selectedImage.mime_type};base64,${selectedImage.data}`}
              alt={selectedImage.prompt || 'Wygenerowany obraz'}
              style={{ 
                width: '100%', 
                borderRadius: 8, 
                border: '1px solid hsl(214, 18%, 88%)',
                display: 'block'
              }}
              data-testid="image-preview"
            />
            <button
              onClick={() => setSelectedImage(null)}
              style={{
                position: 'absolute',
                top: 6,
                right: 6,
                background: 'rgba(0,0,0,0.6)',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: 24,
                height: 24,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
            >
              <X size={14} />
            </button>
          </div>
          <p style={{ fontSize: 11, color: 'hsl(215, 16%, 45%)', marginTop: 6, lineHeight: 1.3 }}>
            {selectedImage.prompt?.slice(0, 80)}{selectedImage.prompt?.length > 80 ? '...' : ''}
          </p>
          <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => handleCopyHtml(selectedImage)} 
              className="gap-1 flex-1"
              data-testid="image-copy-html-button"
            >
              <Copy size={12} /> HTML
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => handleDownload(selectedImage)} 
              className="gap-1 flex-1"
              data-testid="image-download-button"
            >
              <Download size={12} /> Pobierz
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => handleDelete(selectedImage.id)} 
              className="gap-1"
              style={{ color: 'hsl(0, 72%, 51%)' }}
            >
              <Trash2 size={12} />
            </Button>
          </div>
        </div>
      )}

      {/* Image Gallery */}
      <div className="panel-section">
        {loadingImages ? (
          <div style={{ padding: '16px 0' }}>
            <div className="skeleton-line" style={{ height: 60 }} />
            <div className="skeleton-line" style={{ height: 60 }} />
          </div>
        ) : images.length === 0 ? (
          <p style={{ fontSize: 13, color: 'hsl(215, 16%, 45%)', textAlign: 'center', padding: '16px 0' }}>
            Brak obrazów. Kliknij "Generuj" aby utworzyć ilustrację.
          </p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {images.map((image) => (
              <div
                key={image.id}
                onClick={() => loadFullImage(image)}
                style={{
                  borderRadius: 8,
                  overflow: 'hidden',
                  cursor: 'pointer',
                  border: selectedImage?.id === image.id 
                    ? '2px solid hsl(209, 88%, 36%)' 
                    : '1px solid hsl(214, 18%, 88%)',
                  transition: 'border-color 0.15s',
                  position: 'relative'
                }}
                data-testid="image-gallery-item"
              >
                {image.data ? (
                  <img
                    src={`data:${image.mime_type};base64,${image.data}`}
                    alt={image.prompt || 'Obraz'}
                    style={{ width: '100%', height: 80, objectFit: 'cover', display: 'block' }}
                  />
                ) : (
                  <div style={{ 
                    width: '100%', 
                    height: 80, 
                    background: 'hsl(210, 22%, 96%)', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center' 
                  }}>
                    <Image size={20} style={{ color: 'hsl(215, 16%, 65%)' }} />
                  </div>
                )}
                <div style={{ 
                  padding: '4px 6px', 
                  fontSize: 10, 
                  color: 'hsl(215, 16%, 45%)',
                  background: 'white',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {image.style === 'hero' ? 'Hero' : 
                   image.style === 'section' ? 'Sekcja' :
                   image.style === 'infographic' ? 'Info' : 'Własny'}
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
