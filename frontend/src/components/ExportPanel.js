import React, { useState } from 'react';
import { Copy, Download, Loader2, Facebook, Globe, FileCode, FileText } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ExportPanel = ({ articleId }) => {
  const [fbContent, setFbContent] = useState('');
  const [gbContent, setGbContent] = useState('');
  const [loadingFb, setLoadingFb] = useState(false);
  const [loadingGb, setLoadingGb] = useState(false);
  const [loadingHtml, setLoadingHtml] = useState(false);
  const [loadingPdf, setLoadingPdf] = useState(false);

  const generateFacebook = async () => {
    setLoadingFb(true);
    try {
      const res = await axios.post(`${BACKEND_URL}/api/articles/${articleId}/export`, { format: 'facebook' });
      setFbContent(res.data.content);
    } catch (e) {
      toast.error('B\u0142\u0105d generowania posta FB');
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
      toast.error('B\u0142\u0105d generowania posta Google');
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
      toast.error('B\u0142\u0105d pobierania HTML');
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
      toast.error('B\u0142\u0105d pobierania PDF');
    } finally {
      setLoadingPdf(false);
    }
  };

  return (
    <div>
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
