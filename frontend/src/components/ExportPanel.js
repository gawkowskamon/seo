import React, { useState } from 'react';
import { Copy, Download, Loader2, Facebook, Globe, FileCode, FileText, ExternalLink, Check, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const WordPressIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h4l3 9 3-13 3 7 3-3h4" />
  </svg>
);

const ExportPanel = ({ articleId }) => {
  const [fbContent, setFbContent] = useState('');
  const [gbContent, setGbContent] = useState('');
  const [loadingFb, setLoadingFb] = useState(false);
  const [loadingGb, setLoadingGb] = useState(false);
  const [loadingHtml, setLoadingHtml] = useState(false);
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingWp, setLoadingWp] = useState(false);
  const [wpResult, setWpResult] = useState(null);

  const generateFacebook = async () => {
    setLoadingFb(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/export`, { format: 'facebook' });
      setFbContent(res.data.content);
    } catch (e) {
      toast.error('Blad generowania posta FB');
    } finally {
      setLoadingFb(false);
    }
  };

  const generateGoogleBusiness = async () => {
    setLoadingGb(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/export`, { format: 'google_business' });
      setGbContent(res.data.content);
    } catch (e) {
      toast.error('Blad generowania posta Google');
    } finally {
      setLoadingGb(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Skopiowano do schowka');
  };

  const downloadHtml = async () => {
    setLoadingHtml(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/export`, { format: 'html' });
      const blob = new Blob([res.data.content], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'article.html';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('HTML pobrany');
    } catch (e) {
      toast.error('Blad pobierania HTML');
    } finally {
      setLoadingHtml(false);
    }
  };

  const downloadPdf = async () => {
    setLoadingPdf(true);
    try {
      const res = await axios.post(
        `${BACKEND_URL}/api/articles/${articleId}/export`, 
        { format: 'pdf' },
        { responseType: 'blob' }
      );
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'article.pdf';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('PDF pobrany');
    } catch (e) {
      toast.error('Blad pobierania PDF');
    } finally {
      setLoadingPdf(false);
    }
  };

  const publishToWordPress = async () => {
    setLoadingWp(true);
    setWpResult(null);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/publish-wordpress`);
      setWpResult(res.data);
      toast.success('Artykul opublikowany na WordPress jako szkic');
    } catch (e) {
      const msg = e.response?.data?.detail || 'Blad publikacji na WordPress';
      toast.error(msg);
      setWpResult({ success: false, error: msg });
    } finally {
      setLoadingWp(false);
    }
  };

  const downloadWpPlugin = async () => {
    try {
      const res = await axios.get(`${BACKEND_URL}/api/wordpress/plugin`, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'kurdynowski-importer.php';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Wtyczka WordPress pobrana');
    } catch (e) {
      toast.error('Blad pobierania wtyczki');
    }
  };

  return (
    <div>
      {/* WordPress */}
      <div className="panel-section">
        <div className="export-card" data-testid="export-wordpress-card">
          <div className="export-card-header">
            <h4 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <WordPressIcon /> WordPress
            </h4>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
            <Button
              size="sm"
              onClick={publishToWordPress}
              disabled={loadingWp}
              className="gap-1 w-full"
              data-testid="export-wordpress-publish-button"
            >
              {loadingWp ? <Loader2 size={14} className="animate-spin" /> : <ExternalLink size={14} />}
              Opublikuj na WordPress
            </Button>
            {wpResult && wpResult.success && (
              <div style={{
                padding: '8px 10px',
                borderRadius: 8,
                background: 'hsl(142, 50%, 96%)',
                border: '1px solid hsl(142, 50%, 80%)',
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }} data-testid="wp-publish-success">
                <Check size={14} style={{ color: 'hsl(142, 71%, 35%)' }} />
                <div>
                  <div style={{ fontWeight: 600, color: 'hsl(142, 71%, 25%)' }}>Opublikowano jako szkic</div>
                  {wpResult.edit_url && (
                    <a href={wpResult.edit_url} target="_blank" rel="noopener noreferrer"
                      style={{ color: '#04389E', fontSize: 11, textDecoration: 'underline' }}>
                      Edytuj w WordPress
                    </a>
                  )}
                </div>
              </div>
            )}
            {wpResult && !wpResult.success && (
              <div style={{
                padding: '8px 10px',
                borderRadius: 8,
                background: 'hsl(0, 50%, 97%)',
                border: '1px solid hsl(0, 50%, 85%)',
                fontSize: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 6
              }} data-testid="wp-publish-error">
                <AlertCircle size={14} style={{ color: 'hsl(0, 60%, 45%)' }} />
                <div style={{ color: 'hsl(0, 60%, 35%)' }}>
                  {wpResult.error || 'Blad publikacji'}
                </div>
              </div>
            )}
            <div style={{ borderTop: '1px solid hsl(214, 18%, 92%)', paddingTop: 6, marginTop: 2 }}>
              <Button
                variant="ghost"
                size="sm"
                onClick={downloadWpPlugin}
                className="gap-1 w-full"
                style={{ fontSize: 11, color: 'hsl(215, 16%, 45%)' }}
                data-testid="export-wordpress-plugin-button"
              >
                <Download size={12} />
                Pobierz wtyczke WP
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Facebook */}
      <div className="panel-section">
        <div className="export-card" data-testid="export-facebook-card">
          <div className="export-card-header">
            <h4 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Facebook size={16} /> Facebook
            </h4>
            <Button variant="outline" size="sm" onClick={generateFacebook} disabled={loadingFb}>
              {loadingFb ? <Loader2 size={14} className="animate-spin" /> : 'Generuj'}
            </Button>
          </div>
          {fbContent && (
            <>
              <div className="export-preview">{fbContent}</div>
              <div className="export-actions">
                <Button size="sm" variant="outline" onClick={() => copyToClipboard(fbContent)} className="gap-1">
                  <Copy size={14} /> Kopiuj
                </Button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Google Business */}
      <div className="panel-section">
        <div className="export-card" data-testid="export-google-business-card">
          <div className="export-card-header">
            <h4 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Globe size={16} /> Google Business
            </h4>
            <Button variant="outline" size="sm" onClick={generateGoogleBusiness} disabled={loadingGb}>
              {loadingGb ? <Loader2 size={14} className="animate-spin" /> : 'Generuj'}
            </Button>
          </div>
          {gbContent && (
            <>
              <div className="export-preview">{gbContent}</div>
              <div className="export-actions">
                <Button size="sm" variant="outline" onClick={() => copyToClipboard(gbContent)} className="gap-1">
                  <Copy size={14} /> Kopiuj
                </Button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* HTML Download */}
      <div className="panel-section">
        <div className="export-card" data-testid="export-html-download">
          <div className="export-card-header">
            <h4 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <FileCode size={16} /> HTML
            </h4>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={downloadHtml} 
            disabled={loadingHtml}
            className="gap-1 w-full"
            data-testid="export-html-button"
          >
            {loadingHtml ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            Pobierz HTML
          </Button>
        </div>
      </div>

      {/* PDF Download */}
      <div className="panel-section">
        <div className="export-card" data-testid="export-pdf-download">
          <div className="export-card-header">
            <h4 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <FileText size={16} /> PDF
            </h4>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={downloadPdf} 
            disabled={loadingPdf}
            className="gap-1 w-full"
            data-testid="article-export-pdf-button"
          >
            {loadingPdf ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            Pobierz PDF
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ExportPanel;
