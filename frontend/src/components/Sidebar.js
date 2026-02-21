import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, PenTool, Lightbulb, LogOut, User, Layers, Users, Image as ImageIcon, Sparkles, Settings, CreditCard, Calendar, Download, Search, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  
  const navItems = [
    { path: '/', label: 'Pulpit', icon: LayoutDashboard, testId: 'sidebar-nav-dashboard' },
    { path: '/generator', label: 'Nowy artykul', icon: PenTool, testId: 'sidebar-nav-generator' },
    { path: '/series', label: 'Serie', icon: Layers, testId: 'sidebar-nav-series' },
    { path: '/generator-obrazow', label: 'Generator obrazow', icon: Sparkles, testId: 'sidebar-nav-image-generator' },
    { path: '/biblioteka', label: 'Biblioteka', icon: ImageIcon, testId: 'sidebar-nav-library' },
    { path: '/topics', label: 'Tematy', icon: Lightbulb, testId: 'sidebar-nav-topics' },
    { path: '/kalendarz', label: 'Kalendarz', icon: Calendar, testId: 'sidebar-nav-calendar' },
    { path: '/import', label: 'Import', icon: Download, testId: 'sidebar-nav-import' },
    { path: '/audyt-seo', label: 'Audyt SEO', icon: Search, testId: 'sidebar-nav-audit' },
    { path: '/aktualizacje', label: 'Aktualizacje', icon: RefreshCw, testId: 'sidebar-nav-updates' },
    { path: '/cennik', label: 'Cennik', icon: CreditCard, testId: 'sidebar-nav-pricing' },
  ];

  const adminItems = [
    { path: '/admin/users', label: 'Uzytkownicy', icon: Users, testId: 'sidebar-nav-admin-users' },
    { path: '/admin/settings', label: 'Ustawienia', icon: Settings, testId: 'sidebar-nav-admin-settings' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-mark">
            <img src="https://static.prod-images.emergentagent.com/jobs/03a9d366-f1af-4aca-be22-7750e2cedcf9/images/d0d934dc57a3eeae9c2f153104d1f3e94b5ebbbf83e571a8f1bebe771ffb8f14.png" alt="Kurdynowski" />
          </div>
          <div>
            <h1 className="sidebar-brand-name">Kurdynowski<span className="sidebar-brand-dot">.</span></h1>
            <span className="sidebar-brand-desc">Accounting & Tax Solutions</span>
          </div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`sidebar-nav-item ${location.pathname === item.path ? 'active' : ''}`}
            data-testid={item.testId}
          >
            <item.icon size={18} />
            {item.label}
          </Link>
        ))}
        {user?.is_admin && (
          <>
            <div className="sidebar-nav-section-label">Administracja</div>
            {adminItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-nav-item ${location.pathname === item.path ? 'active' : ''}`}
                data-testid={item.testId}
              >
                <item.icon size={18} />
                {item.label}
              </Link>
            ))}
          </>
        )}
      </nav>
      {/* User section at bottom */}
      {user && (
        <div style={{
          padding: '12px 12px 16px',
          borderTop: '1px solid hsl(214, 18%, 88%)',
          marginTop: 'auto'
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '8px 12px', borderRadius: 8,
            background: 'hsl(35, 35%, 97%)', marginBottom: 8
          }}>
            <div style={{
              width: 30, height: 30, borderRadius: '50%',
              background: '#04389E', color: 'white',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 600, flexShrink: 0
            }}>
              {(user.full_name || user.email || '?')[0].toUpperCase()}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'hsl(222, 47%, 11%)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}>
                {user.full_name || 'Uzytkownik'}
                {user.is_admin && (
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 4,
                    background: '#F28C28', color: 'white', letterSpacing: '0.04em'
                  }}>ADMIN</span>
                )}
              </div>
              <div style={{ fontSize: 11, color: 'hsl(215, 16%, 50%)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.email}
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            className="sidebar-nav-item"
            style={{ color: 'hsl(0, 60%, 45%)' }}
            data-testid="sidebar-logout-button"
          >
            <LogOut size={18} />
            Wyloguj
          </button>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
