/**
 * @output-dir src/components
 * @file-naming Layout.jsx
 *
 * PATTERN: Corporate Layout
 * STYLE: corporate
 */

import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/* NAV_LINKS */

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate         = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top navbar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Logo */}
            <span className="text-xl font-bold text-blue-700 tracking-tight">
              /* PROJECT_NAME */
            </span>

            {/* Nav links */}
            <div className="flex gap-6">
              {navLinks.map(link => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    `text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-blue-700 border-b-2 border-blue-700 pb-1'
                        : 'text-gray-600 hover:text-blue-700'
                    }`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </div>

            {/* User + logout */}
            <div className="flex items-center gap-4">
              {user && (
                <span className="text-sm text-gray-500">{user.email}</span>
              )}
              <button
                onClick={handleLogout}
                className="text-sm text-white bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Page content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}