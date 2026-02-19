import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ArticleGenerator from './pages/ArticleGenerator';
import ArticleEditor from './pages/ArticleEditor';
import TopicSuggestions from './pages/TopicSuggestions';
import SeriesGenerator from './pages/SeriesGenerator';
import AuthPage from './pages/AuthPage';
import './App.css';

const ProtectedLayout = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        background: 'hsl(210, 33%, 99%)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14,
            background: '#04389E', color: 'white',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Instrument Serif', Georgia, serif",
            fontSize: 24, marginBottom: 12,
            animation: 'pulse 2s infinite'
          }}>K</div>
          <p style={{ color: 'hsl(215, 16%, 45%)', fontSize: 14 }}>Ladowanie...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-main">
        {children}
      </main>
    </div>
  );
};

function AppRoutes() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return null;
  }

  return (
    <Routes>
      <Route path="/auth" element={
        isAuthenticated ? <Navigate to="/" replace /> : <AuthPage />
      } />
      <Route path="/" element={
        <ProtectedLayout><Dashboard /></ProtectedLayout>
      } />
      <Route path="/generator" element={
        <ProtectedLayout><ArticleGenerator /></ProtectedLayout>
      } />
      <Route path="/editor/:articleId" element={
        <ProtectedLayout><ArticleEditor /></ProtectedLayout>
      } />
      <Route path="/topics" element={
        <ProtectedLayout><TopicSuggestions /></ProtectedLayout>
      } />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="bottom-right" richColors />
      </AuthProvider>
    </Router>
  );
}

export default App;
