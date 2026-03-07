/**
 * @output-dir src/api
 * @file-naming client.js
 *
 * PATTERN: Fetch API client wrapper
 *
 * DEMONSTRATES:
 * - Base URL from env
 * - Auth token injection
 * - JSON request/response handling
 * - Error handling
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

function getToken() {
  return localStorage.getItem('token');
}

async function request(endpoint, options = {}) {
  const token = getToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || 'Request failed');
  }

  return data;
}

export const client = {
  get:    (endpoint)         => request(endpoint),
  post:   (endpoint, body)   => request(endpoint, { method: 'POST',   body: JSON.stringify(body) }),
  put:    (endpoint, body)   => request(endpoint, { method: 'PUT',    body: JSON.stringify(body) }),
  delete: (endpoint)         => request(endpoint, { method: 'DELETE' }),
};