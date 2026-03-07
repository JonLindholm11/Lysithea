/**
 * @output-dir src/api
 * @file-naming auth.api.js
 *
 * PATTERN: Auth API Service
 */

import { client } from './client';

export const authApi = {
  login:    (email, password)           => client.post('/auth/login',    { email, password }),
  register: (email, username, password) => client.post('/auth/register', { email, username, password }),
};