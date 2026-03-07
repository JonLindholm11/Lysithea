/**
 * @output-dir src/pages
 * @file-naming {Resource}Form.jsx
 *
 * PATTERN: Resource Create/Edit Form Page
 * STYLE: corporate
 *
 * DEMONSTRATES:
 * - Single form for create + edit
 * - useParams to detect edit mode
 * - useQuery to load existing record
 * - useMutation for submit
 * - Redirect on success
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useUser, useCreateUser, useUpdateUser } from '../hooks/useUsers';

export default function UserForm() {
  const { id }     = useParams();
  const isEdit     = Boolean(id);
  const navigate   = useNavigate();

  const { data: existing, isLoading } = useUser(id);
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();

  const [form,  setForm]  = useState(/* INITIAL_FORM */);
  const [error, setError] = useState('');

  // Populate form when editing
  useEffect(() => {
    if (existing?.data) {
      setForm(/* POPULATE_FORM */);
    }
  }, [existing]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      if (isEdit) {
        await updateUser.mutateAsync({ id, data: form });
      } else {
        await createUser.mutateAsync(form);
      }
      navigate('/users');
    } catch (err) {
      setError(err.message || 'Save failed');
    }
  }

  if (isEdit && isLoading) return <p className="text-gray-500 text-sm">Loading...</p>;

  const isPending = createUser.isPending || updateUser.isPending;

  return (
    <div className="max-w-xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/users" className="text-sm text-blue-600 hover:underline">
          ← Back to Users
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {isEdit ? 'Edit User' : 'New User'}
      </h1>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        /* FORM_FIELDS */

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium px-5 py-2 rounded transition-colors disabled:opacity-50"
          >
            {isPending ? 'Saving...' : isEdit ? 'Save changes' : 'Create'}
          </button>
          <Link
            to="/users"
            className="text-sm text-gray-600 hover:text-gray-900 px-5 py-2 border border-gray-200 rounded"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}