import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/skills', label: 'Skills' },
    { path: '/settings', label: 'Settings' },
  ];

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="container navbar-content">
        <Link to="/" className="navbar-brand" aria-label="lumen-console home">
          lumen-console
        </Link>
        <div className="navbar-nav">
          {isAuthenticated && navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={location.pathname === item.path ? 'font-medium text-blue-600' : 'text-gray-600 hover:text-gray-900'}
            >
              {item.label}
            </Link>
          ))}
          {isAuthenticated && user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                {user.name || user.preferred_username || user.email || user.sub}
              </span>
              <button onClick={logout} className="btn btn-secondary">
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}