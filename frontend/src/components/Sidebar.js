import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, PenTool, Lightbulb, FileText } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Pulpit', icon: LayoutDashboard, testId: 'sidebar-nav-dashboard' },
    { path: '/generator', label: 'Nowy artyku\u0142', icon: PenTool, testId: 'sidebar-nav-generator' },
    { path: '/topics', label: 'Tematy', icon: Lightbulb, testId: 'sidebar-nav-topics' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <FileText size={20} />
          </div>
          <div>
            <h1>Ksi\u0119gowySEO</h1>
            <span>Generator artyku\u0142\u00f3w</span>
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
      </nav>
    </aside>
  );
};

export default Sidebar;
