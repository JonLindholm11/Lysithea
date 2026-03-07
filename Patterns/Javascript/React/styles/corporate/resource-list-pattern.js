/**
 * @output-dir src/pages
 * @file-naming {Resource}List.jsx
 *
 * PATTERN: Resource List Page
 * STYLE: corporate
 *
 * DEMONSTRATES:
 * - useQuery data table
 * - Pagination controls
 * - Delete with confirmation
 * - Link to detail/edit
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useUsers, useDeleteUser } from '../hooks/useUsers';

export default function UsersList() {
  const [page, setPage]             = useState(1);
  const { data, isLoading, isError } = useUsers(page);
  const deleteUser                   = useDeleteUser();

  const items      = data?.data        ?? [];
  const pagination = data?.pagination  ?? {};

  async function handleDelete(id) {
    if (!confirm('Are you sure?')) return;
    await deleteUser.mutateAsync(id);
  }

  if (isLoading) return <p className="text-gray-500 text-sm">Loading...</p>;
  if (isError)   return <p className="text-red-600  text-sm">Failed to load data.</p>;

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <Link
          to="/users/new"
          className="bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium px-4 py-2 rounded transition-colors"
        >
          + Add User
        </Link>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              /* TABLE_HEADERS */
              <th className="text-left px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.length === 0 && (
              <tr>
                <td colSpan={99} className="px-4 py-6 text-center text-gray-400">
                  No records found.
                </td>
              </tr>
            )}
            {items.map(item => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                /* TABLE_CELLS */
                <td className="px-4 py-3">
                  <div className="flex gap-3">
                    <Link
                      to={`/users/${item.id}`}
                      className="text-blue-600 hover:underline"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="text-red-500 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <div className="flex justify-between items-center mt-4 text-sm text-gray-600">
          <span>
            Page {pagination.page} of {pagination.totalPages} — {pagination.total} total
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => p - 1)}
              disabled={!pagination.hasPrev}
              className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={!pagination.hasNext}
              className="px-3 py-1 border rounded disabled:opacity-40 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}