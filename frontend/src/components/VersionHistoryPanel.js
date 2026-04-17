import React, { useState, useEffect, useCallback } from 'react';
import { History, Loader2, RotateCcw, ChevronDown, ChevronUp, Clock, Wand2, Edit3, Target, Undo2, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SOURCE_META = {
  manual_edit: { label: 'Ręczna edycja', icon: Edit3, color: '#64748b' },
  auto_optimize: { label: '1x Optymalizacja AI', icon: Wand2, color: '#3b82f6' },
  optimize_loop: { label: 'Pętla do 80%+', icon: Target, color: '#f59e0b' },
  pre_restore: { label: 'Przed przywróceniem', icon: Undo2, color: '#94a3b8' },
};

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
    if (!window.confirm('Przywrócić tę wersję? Obecna wersja zostanie zapisana w historii jako "Przed przywróceniem".')) return;
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

  const getScorePct = (v) => {
    const surfer = v?.version_data?.surfer_score?.percentage;
    if (surfer !== undefined && surfer !== null) return surfer;
    return v?.version_data?.seo_score?.percentage;
  };

  return (
    <div className="plagiarism-panel" data-testid="version-history-panel">
      <div className="plagiarism-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <History size={18} style={{ color: '#04389E' }} />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Historia wersji</span>
          {versions.length > 0 && (
            <span style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 10,
              background: 'hsl(220, 95%, 96%)', color: '#04389E', fontWeight: 600
            }}>{versions.length}</span>
          )}
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
        <p className="plagiarism-hint" data-testid="version-history-empty">
          Brak zapisanych wersji. Historia tworzy się automatycznie przy każdym zapisie, optymalizacji lub przywróceniu.
        </p>
      )}

      {!loading && versions.length > 0 && (
        <div style={{ maxHeight: 520, overflowY: 'auto' }}>
          {versions.map((v) => {
            const src = SOURCE_META[v.source] || SOURCE_META.manual_edit;
            const SrcIcon = src.icon;
            const scorePct = getScorePct(v);
            return (
              <div key={v.id} className="version-item" data-testid="version-history-item">
                <button
                  className="version-item-header"
                  onClick={() => loadVersionDetail(v.id)}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '10px 12px', background: 'transparent', border: 'none', cursor: 'pointer', textAlign: 'left', borderBottom: '1px solid hsl(214, 18%, 92%)' }}
                >
                  <div style={{
                    width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: `${src.color}15`, color: src.color
                  }}>
                    <SrcIcon size={14} />
                  </div>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: src.color, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                        {src.label}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 2 }}>
                      <Clock size={11} style={{ color: 'hsl(215, 16%, 55%)', flexShrink: 0 }} />
                      <span style={{ fontSize: 12, color: 'hsl(215, 16%, 35%)' }}>{formatDate(v.created_at)}</span>
                    </div>
                    <div style={{
                      fontSize: 12, color: 'hsl(215, 16%, 55%)', marginTop: 2,
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                    }}>
                      {v.version_data?.title || 'Bez tytułu'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                    {scorePct !== undefined && scorePct !== null && (
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 10,
                        background: scorePct >= 80 ? 'hsl(142, 60%, 92%)' : scorePct >= 50 ? 'hsl(38, 90%, 92%)' : 'hsl(0, 70%, 94%)',
                        color: scorePct >= 80 ? 'hsl(142, 60%, 30%)' : scorePct >= 50 ? 'hsl(38, 80%, 35%)' : 'hsl(0, 70%, 40%)'
                      }}>
                        {scorePct}%
                      </span>
                    )}
                    {expandedVersion === v.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </div>
                </button>

                {expandedVersion === v.id && versionDetail && (
                  <div className="version-detail" style={{ padding: '12px 16px', background: 'hsl(215, 16%, 98%)', borderBottom: '1px solid hsl(214, 18%, 92%)' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8, marginBottom: 10 }}>
                      <div style={{ fontSize: 12 }}>
                        <div style={{ color: 'hsl(215, 16%, 55%)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Sekcje</div>
                        <div style={{ fontWeight: 700, fontSize: 15 }}>{versionDetail.version_data?.sections?.length || 0}</div>
                      </div>
                      <div style={{ fontSize: 12 }}>
                        <div style={{ color: 'hsl(215, 16%, 55%)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>FAQ</div>
                        <div style={{ fontWeight: 700, fontSize: 15 }}>{versionDetail.version_data?.faq?.length || 0}</div>
                      </div>
                      <div style={{ fontSize: 12 }}>
                        <div style={{ color: 'hsl(215, 16%, 55%)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Źródła</div>
                        <div style={{ fontWeight: 700, fontSize: 15 }}>{versionDetail.version_data?.sources?.length || 0}</div>
                      </div>
                      <div style={{ fontSize: 12 }}>
                        <div style={{ color: 'hsl(215, 16%, 55%)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Obrazy</div>
                        <div style={{ fontWeight: 700, fontSize: 15 }}>{versionDetail.version_data?.toc?.length || 0}</div>
                      </div>
                    </div>
                    {versionDetail.version_data?.meta_title && (
                      <div style={{ marginBottom: 8 }}>
                        <div style={{ color: 'hsl(215, 16%, 55%)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Meta tytuł</div>
                        <div style={{ fontSize: 12, color: 'hsl(215, 16%, 25%)' }}>{versionDetail.version_data.meta_title}</div>
                      </div>
                    )}
                    <Button
                      size="sm"
                      className="gap-1 w-full"
                      onClick={() => handleRestore(v.id)}
                      disabled={restoring}
                      data-testid="version-history-restore"
                      style={{ marginTop: 4, background: '#04389E', color: 'white' }}
                    >
                      {restoring ? <Loader2 size={14} className="animate-spin" /> : <RotateCcw size={14} />}
                      Przywróć tę wersję
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default VersionHistoryPanel;
