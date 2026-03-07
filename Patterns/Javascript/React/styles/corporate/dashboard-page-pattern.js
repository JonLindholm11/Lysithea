/**
 * @output-dir src/pages
 * @file-naming Dashboard.jsx
 *
 * PATTERN: Dashboard Page
 * STYLE: corporate
 */

import { useAuth } from '../context/AuthContext';

/* STAT_IMPORTS */

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Welcome back, {user?.username || user?.email}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-/* STAT_COUNT */ gap-6 mb-8">
/* STAT_CARDS */
      </div>

      {/* Quick links */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Quick access</h2>
        <div className="flex flex-wrap gap-3">
/* QUICK_LINKS */
        </div>
      </div>
    </div>
  );
}