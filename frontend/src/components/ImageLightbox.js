import React, { useEffect, useCallback, useState } from 'react';
import { X, ChevronLeft, ChevronRight, Download, Copy, Trash2, Tag, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ImageLightbox = ({ image, images, currentIndex, onClose, onNavigate, onDelete, onTagsUpdate }) => {
  const [loadedImage, setLoadedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTagEditor, setShowTagEditor] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState(image?.tags || []);

  const loadFullImage = useCallback(async (img) => {
    if (img?.data && img.data.length > 300) {
      setLoadedImage(img);
      return;
    }
    setLoading(true);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/images/${img.id}`);
      setLoadedImage(res.data);
    } catch (err) {
      toast.error('Blad ladowania obrazu');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (image) {
      loadFullImage(image);
      setTags(image.tags || []);
    }
  }, [image, loadFullImage]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
    if (e.key === 'ArrowLeft' && currentIndex > 0) onNavigate(currentIndex - 1);
    if (e.key === 'ArrowRight' && images && currentIndex < images.length - 1) onNavigate(currentIndex + 1);
  }, [onClose, onNavigate, currentIndex, images]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  const handleCopyHtml = () => {
    if (!loadedImage) return;
    const html = `<img src="data:${loadedImage.mime_type};base64,${loadedImage.data}" alt="${loadedImage.prompt || ''}" style="max-width: 100%; height: auto;" />`;
    navigator.clipboard.writeText(html);
    toast.success('HTML skopiowany do schowka');
  };

  const handleDownload = () => {
    if (!loadedImage) return;
    const link = document.createElement('a');
    link.href = `data:${loadedImage.mime_type};base64,${loadedImage.data}`;
    link.download = `image-${loadedImage.id || 'download'}.${loadedImage.mime_type?.split('/')[1] || 'png'}`;
    link.click();
    toast.success('Pobieranie rozpoczete');
  };

  const handleAddTag = async () => {
    if (!tagInput.trim() || !image?.id) return;
    const newTags = [...new Set([...tags, tagInput.trim().toLowerCase()])];
    try {
      await axios.put(`${BACKEND_URL}/api/images/${image.id}/tags`, { tags: newTags });
      setTags(newTags);
      setTagInput('');
      if (onTagsUpdate) onTagsUpdate(image.id, newTags);
      toast.success('Tag dodany');
    } catch (err) {
      toast.error('Blad dodawania tagu');
    }
  };

  const handleRemoveTag = async (tagToRemove) => {
    if (!image?.id) return;
    const newTags = tags.filter(t => t !== tagToRemove);
    try {
      await axios.put(`${BACKEND_URL}/api/images/${image.id}/tags`, { tags: newTags });
      setTags(newTags);
      if (onTagsUpdate) onTagsUpdate(image.id, newTags);
    } catch (err) {
      toast.error('Blad usuwania tagu');
    }
  };

  if (!image) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0,0,0,0.85)',
        backdropFilter: 'blur(12px)',
      }}
      onClick={onClose}
      data-testid="image-lightbox-overlay"
    >
      <div
        style={{
          position: 'relative',
          maxWidth: '90vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: -44,
            right: 0,
            width: 36,
            height: 36,
            borderRadius: 10,
            background: 'rgba(255,255,255,0.15)',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background-color 0.15s'
          }}
          data-testid="lightbox-close-button"
        >
          <X size={20} />
        </button>

        {/* Navigation arrows */}
        {images && currentIndex > 0 && (
          <button
            onClick={() => onNavigate(currentIndex - 1)}
            style={{
              position: 'absolute',
              left: -56,
              top: '50%',
              transform: 'translateY(-50%)',
              width: 44,
              height: 44,
              borderRadius: 12,
              background: 'rgba(255,255,255,0.15)',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background-color 0.15s'
            }}
            data-testid="lightbox-prev-button"
          >
            <ChevronLeft size={24} />
          </button>
        )}
        {images && currentIndex < images.length - 1 && (
          <button
            onClick={() => onNavigate(currentIndex + 1)}
            style={{
              position: 'absolute',
              right: -56,
              top: '50%',
              transform: 'translateY(-50%)',
              width: 44,
              height: 44,
              borderRadius: 12,
              background: 'rgba(255,255,255,0.15)',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background-color 0.15s'
            }}
            data-testid="lightbox-next-button"
          >
            <ChevronRight size={24} />
          </button>
        )}

        {/* Image */}
        {loading ? (
          <div style={{ width: 400, height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Loader2 size={32} className="animate-spin" style={{ color: 'white' }} />
          </div>
        ) : loadedImage ? (
          <img
            src={`data:${loadedImage.mime_type};base64,${loadedImage.data}`}
            alt={loadedImage.prompt || ''}
            style={{
              maxWidth: '80vw',
              maxHeight: '70vh',
              borderRadius: 12,
              objectFit: 'contain',
              boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
            }}
            data-testid="lightbox-image"
          />
        ) : null}

        {/* Bottom info bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          background: 'rgba(255,255,255,0.1)',
          backdropFilter: 'blur(8px)',
          borderRadius: 12,
          padding: '10px 16px',
          color: 'white',
          maxWidth: '80vw',
          width: '100%'
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {image.prompt || 'Bez opisu'}
            </div>
            <div style={{ fontSize: 11, opacity: 0.7, display: 'flex', gap: 8, marginTop: 2 }}>
              <span>{image.style || 'custom'}</span>
              {image.created_at && <span>{new Date(image.created_at).toLocaleDateString('pl-PL')}</span>}
              {images && <span>{currentIndex + 1} / {images.length}</span>}
            </div>
            {/* Tags */}
            {tags.length > 0 && (
              <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap' }}>
                {tags.map(t => (
                  <span
                    key={t}
                    onClick={() => handleRemoveTag(t)}
                    style={{
                      fontSize: 10,
                      padding: '2px 8px',
                      borderRadius: 6,
                      background: 'rgba(242, 140, 40, 0.3)',
                      color: '#F28C28',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s'
                    }}
                  >
                    {t} x
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 6 }}>
            <button
              onClick={() => setShowTagEditor(!showTagEditor)}
              style={{
                width: 34, height: 34, borderRadius: 8,
                background: showTagEditor ? 'rgba(242, 140, 40, 0.3)' : 'rgba(255,255,255,0.15)',
                color: 'white', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}
              data-testid="lightbox-tag-button"
            >
              <Tag size={16} />
            </button>
            <button
              onClick={handleCopyHtml}
              style={{
                width: 34, height: 34, borderRadius: 8,
                background: 'rgba(255,255,255,0.15)',
                color: 'white', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}
              data-testid="lightbox-copy-button"
            >
              <Copy size={16} />
            </button>
            <button
              onClick={handleDownload}
              style={{
                width: 34, height: 34, borderRadius: 8,
                background: 'rgba(255,255,255,0.15)',
                color: 'white', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}
              data-testid="lightbox-download-button"
            >
              <Download size={16} />
            </button>
            {onDelete && (
              <button
                onClick={() => { onDelete(image.id); onClose(); }}
                style={{
                  width: 34, height: 34, borderRadius: 8,
                  background: 'rgba(220, 50, 50, 0.3)',
                  color: 'white', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}
                data-testid="lightbox-delete-button"
              >
                <Trash2 size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Tag editor */}
        {showTagEditor && (
          <div style={{
            display: 'flex',
            gap: 8,
            background: 'rgba(255,255,255,0.1)',
            backdropFilter: 'blur(8px)',
            borderRadius: 10,
            padding: '8px 12px',
            width: '100%',
            maxWidth: '80vw'
          }}>
            <Input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddTag()}
              placeholder="Dodaj tag..."
              style={{ flex: 1, background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', fontSize: 13 }}
              data-testid="lightbox-tag-input"
            />
            <Button size="sm" onClick={handleAddTag} style={{ background: '#F28C28', fontSize: 12 }} data-testid="lightbox-tag-add-button">
              Dodaj
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImageLightbox;
