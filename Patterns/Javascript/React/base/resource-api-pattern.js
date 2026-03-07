/**
 * @output-dir src/api
 * @file-naming {resource}.api.js
 *
 * PATTERN: Resource API Service
 *
 * DEMONSTRATES:
 * - All CRUD operations for a resource
 * - Uses shared client wrapper
 * - Clean function names for react-query
 */

import { client } from './client';

export const usersApi = {
  getAll:   (page = 1, limit = 20) => client.get(`/users?page=${page}&limit=${limit}`),
  getById:  (id)                   => client.get(`/users/${id}`),
  create:   (data)                 => client.post('/users', data),
  update:   (id, data)             => client.put(`/users/${id}`, data),
  delete:   (id)                   => client.delete(`/users/${id}`),
};