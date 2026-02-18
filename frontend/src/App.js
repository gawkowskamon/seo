import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ArticleGenerator from './pages/ArticleGenerator';
import ArticleEditor from './pages/ArticleEditor';
import TopicSuggestions from './pages/TopicSuggestions';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generator" element={<ArticleGenerator />} />
            <Route path="/editor/:articleId" element={<ArticleEditor />} />
            <Route path="/topics" element={<TopicSuggestions />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
        <Toaster position="bottom-right" richColors />
      </div>
    </Router>
  );
}

export default App;
