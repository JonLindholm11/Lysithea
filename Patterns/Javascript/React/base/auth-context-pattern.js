/**
 * @output-dir src/context
 * @file-naming AuthContext.jsx
 *
 * PATTERN: Auth Context
 *
 * DEMONSTRATES:
 * - JWT token storage in localStorage
 * - Login / logout / register actions
 * - Current user state
 * - Protected route support
 */

import { createContext, useContext, useState } from 'react';
import { client } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,  setUser]  = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });

  async function login(email, password) {
    const res = await client.post('/auth/login', { email, password });
    localStorage.setItem('token', res.token);
    localStorage.setItem('user',  JSON.stringify(res.data));
    setUser(res.data);
    return res;
  }

  async function register(email, username, password) {
    const res = await client.post('/auth/register', { email, username, password });
    localStorage.setItem('token', res.token);
    localStorage.setItem('user',  JSON.stringify(res.data));
    setUser(res.data);
    return res;
  }

  function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}