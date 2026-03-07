/**
 * @output-dir api/routes
 * @file-naming auth.js
 *
 * PATTERN: Express Authentication Routes (Register + Login)
 *
 * USE WHEN:
 * - Project has a users table
 * - Need register and login endpoints
 * - Using JWT for authentication
 * - Using bcrypt for password hashing
 *
 * DEMONSTRATES:
 * - POST /auth/register — creates user, returns user object + JWT
 * - POST /auth/login — validates credentials, returns user object + JWT
 * - Input validation
 * - Password hashing with bcrypt
 * - JWT signing with expiry
 * - Proper HTTP status codes (201, 200, 400, 401, 409, 500)
 * - Never returning password_hash to client
 *
 * SECURITY NOTES:
 * - Never store plain text passwords
 * - Use bcrypt with salt rounds >= 10
 * - Sign JWT with secret from environment variable
 * - Set token expiry (e.g. 7d)
 * - Never expose password_hash in response
 */

const express = require('express');
const router  = express.Router();
const bcrypt  = require('bcrypt');
const jwt     = require('jsonwebtoken');

/**
 * POST /auth/register
 *
 * Request body:
 * { "email": "user@example.com", "username": "user1", "password": "securepass" }
 *
 * Success (201):
 * { "data": { "id": 1, "email": "...", "username": "..." }, "token": "..." }
 *
 * Errors: 400 missing fields, 409 duplicate email
 */
router.post('/register', async (req, res) => {
  try {
    const { email, username, password } = req.body;

    // Validate required fields
    if (!email || !username || !password) {
      return res.status(400).json({
        error:    'Missing required fields',
        code:     'MISSING_FIELDS',
        required: ['email', 'username', 'password'],
      });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({
        error: 'Invalid email format',
        code:  'INVALID_EMAIL',
      });
    }

    // Validate password length
    if (password.length < 8) {
      return res.status(400).json({
        error: 'Password must be at least 8 characters',
        code:  'INVALID_PASSWORD',
      });
    }

    // Check for existing user
    const existing = await getUserByEmail(email);
    if (existing) {
      return res.status(409).json({
        error: 'Email already registered',
        code:  'DUPLICATE_EMAIL',
      });
    }

    // Hash password and create user
    const password_hash = await bcrypt.hash(password, 10);
    const user          = await createUser({ email, username, password_hash });

    // Sign JWT
    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    // Never return password_hash
    delete user.password_hash;

    res.status(201).json({ data: user, token });
  } catch (error) {
    console.error('Error registering user:', error);
    res.status(500).json({
      error: 'Registration failed',
      code:  'REGISTER_ERROR',
    });
  }
});

/**
 * POST /auth/login
 *
 * Request body:
 * { "email": "user@example.com", "password": "securepass" }
 *
 * Success (200):
 * { "data": { "id": 1, "email": "...", "username": "..." }, "token": "..." }
 *
 * Errors: 400 missing fields, 401 invalid credentials
 */
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate required fields
    if (!email || !password) {
      return res.status(400).json({
        error:    'Missing required fields',
        code:     'MISSING_FIELDS',
        required: ['email', 'password'],
      });
    }

    // Find user
    const user = await getUserByEmail(email);
    if (!user) {
      return res.status(401).json({
        error: 'Invalid email or password',
        code:  'INVALID_CREDENTIALS',
      });
    }

    // Verify password
    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      return res.status(401).json({
        error: 'Invalid email or password',
        code:  'INVALID_CREDENTIALS',
      });
    }

    // Sign JWT
    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    // Never return password_hash
    delete user.password_hash;

    res.status(200).json({ data: user, token });
  } catch (error) {
    console.error('Error logging in:', error);
    res.status(500).json({
      error: 'Login failed',
      code:  'LOGIN_ERROR',
    });
  }
});

module.exports = router;