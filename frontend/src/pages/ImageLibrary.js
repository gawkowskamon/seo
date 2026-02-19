import React, { useState, useEffect, useCallback } from 'react';
import { Image as ImageIcon, Search, Filter, Tag, Loader2, Trash2, Grid3X3, List, Download, Copy, Wand2, Scissors, SunMedium, Palette as PaletteIcon, RotateCcw, X, ChevronDown } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import ImageLightbox from '../components/ImageLightbox';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const EDIT_MODES = [
  { id: 'inpaint', label: 'Modyfikuj fragment', icon: Wand2, desc: 'Zmien czesc obrazu na podstawie opisu', placeholder: 'Np. Dodaj wykres w prawym gornym rogu' },
  { id: 'background', label: 'Zmien tlo', icon: SunMedium, desc: 'Zamien tlo zachowujac glowny element', placeholder: 'Np. Tlo biurowe z duzymi oknami' },
  { id: 'style_transfer', label: 'Transfer stylu', icon: PaletteIcon, desc: 'Zmien styl artystyczny obrazu', placeholder: 'Np. Styl minimalistyczny flat design' },
  { id: 'enhance', label: 'Ulepsz', icon: RotateCcw, desc: 'Popraw jakosc i detale', placeholder: 'Np. Popraw ostrość i nasycenie kolorow' },
];

export default function ImageLibrary() {
  const { user } = useAuth();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [activeTag, setActiveTag] = useState('');
  const [allTags, setAllTags] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  // Lightbox
  const [lightboxImage, setLightboxImage] = useState(null);
  const [lightboxIndex, setLightboxIndex] = useState(0);

  // AI Edit dialog
  const [editDialog, setEditDialog] = useState(null); // { imageId, mode }
  const [editPrompt, setEditPrompt] = useState('');
  const [editing, setEditing] = useState(false);

  const LIMIT = 30;

  const fetchImages = useCallback(async (resetOffset = false) => {
    setLoading(true);
    try {
      const params = { limit: LIMIT, offset: resetOffset ? 0 : offset };
      if (searchQuery) params.q = searchQuery;
      if (activeFilter) params.style = activeFilter;
      if (activeTag) params.tag = activeTag;
      const res = await axios.get(`${BACKEND_URL}/api/library/images`, { params });
      setImages(res.data.images);
      setTotal(res.data.total);
      if (resetOffset) setOffset(0);
    } catch (err) {
      toast.error('Blad ladowania biblioteki');
    } finally {
      setLoading(false);
    }
  }, [offset, searchQuery, activeFilter, activeTag]);

  const fetchTags = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/library/tags`);
      setAllTags(res.data);
    } catch (err) { /* ignore */ }
  };

  useEffect(() => {
    fetchImages(true);
    fetchTags();
  }, [searchQuery, activeFilter, activeTag]);

  useEffect(() => {
    if (offset > 0) fetchImages();
  }, [offset]);

  const handleDelete = async (imageId) => {
    try {
      await axios.delete(`${BACKEND_URL}/api/images/${imageId}`);
      setImages(prev => prev.filter(img => img.id !== imageId));
      setTotal(prev => prev - 1);
      toast.success('Obraz usuniety');
    } catch (err) {
      toast.error('Blad usuwania');
    }
  };

  const handleTagsUpdate = (imageId, newTags) => {
    setImages(prev => prev.map(img => img.id === imageId ? { ...img, tags: newTags } : img));
    fetchTags();
  };

  const handleCopyHtml = async (img) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/images/${img.id}`);
      const html = `<img src="data:${res.data.mime_type};base64,${res.data.data}" alt="${res.data.prompt || ''}" style="max-width: 100%; height: auto;" />`;
      navigator.clipboard.writeText(html);
      toast.success('HTML skopiowany');
    } catch (err) {
      toast.error('Blad kopiowania');
    }
  };

  const handleDownload = async (img) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/images/${img.id}`);
      const link = document.createElement('a');
      link.href = `data:${res.data.mime_type};base64,${res.data.data}`;
      link.download = `image-${img.id}.${res.data.mime_type?.split('/')[1] || 'png'}`;
      link.click();
      toast.success('Pobieranie rozpoczete');
    } catch (err) {
      toast.error('Blad pobierania');
    }
  };

  const handleAiEdit = async () => {
    if (!editDialog || !editPrompt.trim()) return;
    setEditing(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/images/edit`, {
        mode: editDialog.mode,
        prompt: editPrompt.trim(),
        image_id: editDialog.imageId
      }, { timeout: 120000 });
      toast.success('Obraz zmodyfikowany');
      setEditDialog(null);
      setEditPrompt('');
      // Show in lightbox
      setLightboxImage(res.data);
      setLightboxIndex(-1);
      // Refresh library
      fetchImages(true);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Blad edycji obrazu';
      toast.error(msg);
    } finally {
      setEditing(false);
    }
  };

  const openLightbox = async (img, index) => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/images/${img.id}`);
      setLightboxImage({ ...img, ...res.data });
      setLightboxIndex(index);
    } catch (err) {
      toast.error('Blad ladowania obrazu');
    }
  };

  const navigateLightbox = async (newIndex) => {
    const img = images[newIndex];
    if (!img) return;
    try {
      const res = await axios.get(`${BACKEND_URL}/api/images/${img.id}`);
      setLightboxImage({ ...img, ...res.data });
      setLightboxIndex(newIndex);
    } catch (err) {
      toast.error('Blad ladowania obrazu');
    }
  };

  const STYLES = ['hero', 'fotorealizm', 'ilustracja', 'infografika', 'ikona', 'diagram', 'wykres', 'custom'];

  return (
    <div className="page-container" data-testid="image-library-page">
      <div className="page-header">
        <h1>Biblioteka obrazow</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Badge variant="outline" style={{ fontSize: 12 }}>{total} obrazow</Badge>
        </div>
      </div>

      {/* Search and filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: '1 1 280px', maxWidth: 400 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'hsl(215, 16%, 55%)' }} />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Szukaj po opisie..."
            style={{ paddingLeft: 36 }}
            data-testid="library-search-input"
          />
        </div>
        <Button
          variant={showFilters ? "default" : "outline"}
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className="gap-1"
          data-testid="library-toggle-filters-button"
        >
          <Filter size={14} />
          Filtry
          {(activeFilter || activeTag) && (
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: '#F28C28', marginLeft: 2
            }} />
          )}
        </Button>
        {(activeFilter || activeTag) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setActiveFilter(''); setActiveTag(''); }}
            className="gap-1"
            style={{ color: 'hsl(0, 60%, 45%)' }}
            data-testid="library-clear-filters-button"
          >
            <X size={14} />
            Wyczysc
          </Button>
        )}
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div style={{
          background: 'hsl(35, 35%, 97%)',
          borderRadius: 12,
          padding: 16,
          marginBottom: 20,
          border: '1px solid hsl(214, 18%, 88%)'
        }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'hsl(215, 16%, 50%)', marginBottom: 8 }}>
              Styl
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {STYLES.map(s => (
                <button
                  key={s}
                  onClick={() => setActiveFilter(activeFilter === s ? '' : s)}
                  style={{
                    padding: '4px 12px',
                    borderRadius: 6,
                    border: activeFilter === s ? '2px solid #04389E' : '1px solid hsl(214, 18%, 88%)',
                    background: activeFilter === s ? 'hsl(220, 95%, 98%)' : 'white',
                    cursor: 'pointer',
                    fontSize: 12,
                    fontWeight: activeFilter === s ? 600 : 400,
                    color: activeFilter === s ? '#04389E' : 'hsl(215, 16%, 45%)',
                    transition: 'border-color 0.15s, color 0.15s'
                  }}
                  data-testid={`library-filter-style-${s}`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          {allTags.length > 0 && (
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'hsl(215, 16%, 50%)', marginBottom: 8 }}>
                Tagi
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {allTags.map(t => (
                  <button
                    key={t.tag}
                    onClick={() => setActiveTag(activeTag === t.tag ? '' : t.tag)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: 6,
                      border: activeTag === t.tag ? '2px solid #F28C28' : '1px solid hsl(214, 18%, 88%)',
                      background: activeTag === t.tag ? 'hsl(34, 90%, 96%)' : 'white',
                      cursor: 'pointer',
                      fontSize: 12,
                      fontWeight: activeTag === t.tag ? 600 : 400,
                      color: activeTag === t.tag ? '#F28C28' : 'hsl(215, 16%, 45%)',
                      transition: 'border-color 0.15s, color 0.15s'
                    }}
                    data-testid={`library-filter-tag-${t.tag}`}
                  >
                    {t.tag} ({t.count})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Images grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <Loader2 size={32} className="animate-spin" style={{ color: '#04389E', margin: '0 auto' }} />
          <p style={{ color: 'hsl(215, 16%, 50%)', fontSize: 14, marginTop: 12 }}>Ladowanie biblioteki...</p>
        </div>
      ) : images.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <ImageIcon size={48} style={{ color: 'hsl(215, 16%, 75%)', margin: '0 auto 12px', display: 'block' }} />
          <h3 style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 22, color: 'hsl(222, 47%, 11%)', marginBottom: 8 }}>
            Brak obrazow
          </h3>
          <p style={{ color: 'hsl(215, 16%, 50%)', fontSize: 14 }}>
            {searchQuery || activeFilter || activeTag ? 'Brak wynikow dla wybranych filtrow.' : 'Wygeneruj obrazy w edytorze artykulow, a pojawia sie tutaj.'}
          </p>
        </div>
      ) : (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 16
          }}>
            {images.map((img, idx) => (
              <div
                key={img.id}
                style={{
                  borderRadius: 12,
                  overflow: 'hidden',
                  border: '1px solid hsl(214, 18%, 88%)',
                  background: 'white',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s, transform 0.2s',
                  position: 'relative'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 12px 30px rgba(15,23,42,0.10)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'none';
                }}
                data-testid="library-image-card"
              >
                {/* Image thumbnail */}
                <div
                  onClick={() => openLightbox(img, idx)}
                  style={{
                    width: '100%',
                    aspectRatio: '4/3',
                    background: 'hsl(35, 35%, 97%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden'
                  }}
                >
                  {img.has_data ? (
                    <img
                      src={`data:${img.mime_type};base64,${img.data || ''}`}
                      alt={img.prompt || ''}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      loading="lazy"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <ImageIcon size={28} style={{ color: 'hsl(215, 16%, 75%)' }} />
                  )}
                </div>

                {/* Info */}
                <div style={{ padding: '10px 12px' }}>
                  <div style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'hsl(222, 47%, 11%)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    marginBottom: 4
                  }}>
                    {img.prompt || 'Bez opisu'}
                  </div>
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center', marginBottom: 6 }}>
                    <Badge variant="outline" style={{ fontSize: 10, padding: '1px 6px' }}>
                      {img.style || 'custom'}
                    </Badge>
                    {img.created_at && (
                      <span style={{ fontSize: 10, color: 'hsl(215, 16%, 55%)' }}>
                        {new Date(img.created_at).toLocaleDateString('pl-PL')}
                      </span>
                    )}
                  </div>
                  {/* Tags */}
                  {img.tags && img.tags.length > 0 && (
                    <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', marginBottom: 6 }}>
                      {img.tags.slice(0, 3).map(t => (
                        <span key={t} style={{
                          fontSize: 10, padding: '1px 6px', borderRadius: 4,
                          background: 'hsl(34, 90%, 96%)', color: '#F28C28'
                        }}>
                          {t}
                        </span>
                      ))}
                      {img.tags.length > 3 && (
                        <span style={{ fontSize: 10, color: 'hsl(215, 16%, 55%)' }}>
                          +{img.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                  {/* Actions */}
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleCopyHtml(img); }}
                      style={{
                        flex: 1, padding: '5px 0', borderRadius: 6,
                        border: '1px solid hsl(214, 18%, 88%)',
                        background: 'white', cursor: 'pointer',
                        fontSize: 10, color: 'hsl(215, 16%, 45%)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3,
                        transition: 'border-color 0.15s'
                      }}
                      data-testid="library-copy-html-button"
                    >
                      <Copy size={11} /> HTML
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDownload(img); }}
                      style={{
                        flex: 1, padding: '5px 0', borderRadius: 6,
                        border: '1px solid hsl(214, 18%, 88%)',
                        background: 'white', cursor: 'pointer',
                        fontSize: 10, color: 'hsl(215, 16%, 45%)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3,
                        transition: 'border-color 0.15s'
                      }}
                      data-testid="library-download-button"
                    >
                      <Download size={11} /> Pobierz
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditDialog({ imageId: img.id, mode: 'inpaint' });
                        setEditPrompt('');
                      }}
                      style={{
                        flex: 1, padding: '5px 0', borderRadius: 6,
                        border: '1px solid hsl(214, 18%, 88%)',
                        background: 'white', cursor: 'pointer',
                        fontSize: 10, color: '#04389E',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 3,
                        fontWeight: 600,
                        transition: 'border-color 0.15s'
                      }}
                      data-testid="library-edit-button"
                    >
                      <Wand2 size={11} /> Edytuj
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDelete(img.id); }}
                      style={{
                        width: 30, padding: '5px 0', borderRadius: 6,
                        border: '1px solid hsl(214, 18%, 88%)',
                        background: 'white', cursor: 'pointer',
                        color: 'hsl(0, 60%, 45%)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        transition: 'border-color 0.15s'
                      }}
                      data-testid="library-delete-button"
                    >
                      <Trash2 size={11} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > LIMIT && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 24 }}>
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                data-testid="library-prev-page"
              >
                Poprzednia
              </Button>
              <span style={{ fontSize: 13, color: 'hsl(215, 16%, 50%)', display: 'flex', alignItems: 'center' }}>
                {offset + 1}-{Math.min(offset + LIMIT, total)} z {total}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + LIMIT >= total}
                onClick={() => setOffset(offset + LIMIT)}
                data-testid="library-next-page"
              >
                Nastepna
              </Button>
            </div>
          )}
        </>
      )}

      {/* Lightbox */}
      {lightboxImage && (
        <ImageLightbox
          image={lightboxImage}
          images={images}
          currentIndex={lightboxIndex}
          onClose={() => setLightboxImage(null)}
          onNavigate={navigateLightbox}
          onDelete={handleDelete}
          onTagsUpdate={handleTagsUpdate}
        />
      )}

      {/* AI Edit Dialog */}
      <Dialog open={!!editDialog} onOpenChange={(open) => { if (!open) { setEditDialog(null); setEditPrompt(''); } }}>
        <DialogContent style={{ maxWidth: 520 }}>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: 22 }}>
              Edycja obrazu AI
            </DialogTitle>
          </DialogHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: '4px 0' }}>
            {/* Mode selector */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
              {EDIT_MODES.map(mode => {
                const MIcon = mode.icon;
                const isSelected = editDialog?.mode === mode.id;
                return (
                  <button
                    key={mode.id}
                    onClick={() => setEditDialog(prev => prev ? { ...prev, mode: mode.id } : null)}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 8,
                      padding: '10px 12px',
                      borderRadius: 10,
                      border: isSelected ? '2px solid #04389E' : '1px solid hsl(214, 18%, 88%)',
                      background: isSelected ? 'hsl(220, 95%, 98%)' : 'white',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'border-color 0.15s'
                    }}
                    data-testid={`edit-mode-${mode.id}`}
                  >
                    <MIcon size={16} style={{ color: isSelected ? '#04389E' : 'hsl(215, 16%, 50%)', marginTop: 1, flexShrink: 0 }} />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: isSelected ? 600 : 500, color: isSelected ? '#04389E' : 'hsl(222, 47%, 11%)' }}>
                        {mode.label}
                      </div>
                      <div style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', marginTop: 2 }}>
                        {mode.desc}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Prompt */}
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', display: 'block', marginBottom: 6 }}>
                Opis zmian
              </label>
              <textarea
                value={editPrompt}
                onChange={(e) => setEditPrompt(e.target.value)}
                placeholder={EDIT_MODES.find(m => m.id === editDialog?.mode)?.placeholder || 'Opisz zmiany...'}
                rows={3}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 8,
                  border: '1px solid hsl(214, 18%, 88%)',
                  fontSize: 13,
                  resize: 'vertical',
                  fontFamily: 'inherit',
                  outline: 'none'
                }}
                data-testid="edit-prompt-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setEditDialog(null); setEditPrompt(''); }}>Anuluj</Button>
            <Button
              onClick={handleAiEdit}
              disabled={editing || !editPrompt.trim()}
              className="gap-1"
              data-testid="edit-submit-button"
            >
              {editing ? <Loader2 size={14} className="animate-spin" /> : <Wand2 size={14} />}
              {editing ? 'Przetwarzanie...' : 'Zastosuj'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
