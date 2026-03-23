import React, { useState, useEffect, useCallback } from 'react';
import { History, Loader2, RotateCcw, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const VersionHistoryPanel = ({ articleId, onRestore }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedVersion, setExpandedVersion] = useState(null);
  const [versionDetail, setVersionDetail] = useState(null);
  const [restoring, setRestoring] = useState(false);

  const fetchVersions = useCallback(async () => {
    if (!articleId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/${articleId}/versions`);
      setVersions(res.data || []);
    } catch {
      // No versions yet
    } finally {
      setLoading(false);
    }
  }, [articleId]);

  useEffect(() => { fetchVersions(); }, [fetchVersions]);

  const loadVersionDetail = async (versionId) => {
    if (expandedVersion === versionId) {
      setExpandedVersion(null);
      setVersionDetail(null);
      return;
    }
    try {
      const res = await axios.get(`${BACKEND_URL}/api/articles/${articleId}/versions/${versionId}`);
      setVersionDetail(res.data);
      setExpandedVersion(versionId);
    } catch {
      toast.error('Błąd ładowania wersji');
    }
  };

  const handleRestore = async (versionId) => {
    if (!window.confirm('Przywrócić tę wersję? Obecna wersja zostanie zapisana w historii.')) return;
    setRestoring(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/versions/${versionId}/restore`);
      toast.success('Wersja przywrócona');
      if (onRestore) onRestore(res.data);
      fetchVersions();
    } catch {
      toast.error('Błąd przywracania wersji');
    } finally {
      setRestoring(false);
    }
  };

  const formatDate = (d) => {
    if (!d) return '';
    return new Date(d).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="plagiarism-panel" data-testid="version-history-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <History size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Historia wersji</span>
        </div>
        <Button size="sm" variant="outline" onClick={fetchVersions} disabled={loading} className="gap-1" data-testid="version-history-refresh">
          <RotateCcw size={14} /> Odśwież
        </Button>
      </div>

      {loading && (
        <div className="plagiarism-loading">
          <Loader2 size={20} className="animate-spin" />
        </div>
      )}

      {!loading && versions.length === 0 && (
        <p className="plagiarism-hint">Brak zapisanych wersji. Historia tworzy się automatycznie przy każdym zapisie artykułu.</p>
      )}

      {!loading && versions.length > 0 && (
        <div style={{ maxHeight: 400, overflowY: 'auto' }}>
          {versions.map((v, idx) => (
            <div key={v.id} className="version-item" data-testid="version-history-item">
              <button className="version-item-header" onClick={() => loadVersionDetail(v.id)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                  <Clock size={13} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                  <div style={{ minWidth: 0 }}>
                    <span className="version-date">{formatDate(v.created_at)}</span>
                    <span className="version-title">{v.version_data?.title || 'Bez tytułu'}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {v.version_data?.seo_score?.percentage !== undefined && (
                    <span className={`seo-badge ${v.version_data.seo_score.percentage >= 80 ? 'high' : v.version_data.seo_score.percentage >= 50 ? 'medium' : 'low'}`} style={{ fontSize: 10 }}>
                      {v.version_data.seo_score.percentage}%
                    </span>
                  )}
                  {expandedVersion === v.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>
              </button>

              {expandedVersion === v.id && versionDetail && (
                <div className="version-detail">
                  <div className="version-detail-row">
                    <span>Tytuł:</span> <strong>{versionDetail.version_data?.title || '-'}</strong>
                  </div>
                  <div className="version-detail-row">
                    <span>Sekcje:</span> <strong>{versionDetail.version_data?.sections?.length || 0}</strong>
                  </div>
                  <div className="version-detail-row">
                    <span>FAQ:</span> <strong>{versionDetail.version_data?.faq?.length || 0}</strong>
                  </div>
                  <div className="version-detail-row">
                    <span>Źródła:</span> <strong>{versionDetail.version_data?.sources?.length || 0}</strong>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="gap-1 w-full"
                    onClick={() => handleRestore(v.id)}
                    disabled={restoring}
                    data-testid="version-history-restore"
                    style={{ marginTop: 8 }}
                  >
                    {restoring ? <Loader2 size={14} className="animate-spin" /> : <RotateCcw size={14} />}
                    Przywróć tę wersję
                  </Button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default VersionHistoryPanel;
