// patterns/javascript/express/routes/post-users-auth.js

/**
 * @output-dir api/routes
 * @file-naming {resource}.js
 * 
 * PATTERN: Express POST Route with Authentication and Validation
 *
 * USE WHEN:
 * - Creating new resources in database
 * - Route requires authentication (JWT)
 * - Need input validation and sanitization
 * - Using PostgreSQL with raw SQL queries
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - Request body validation
 * - Parameterized SQL queries (SQL injection safe)
 * - Error handling with try/catch
 * - Proper HTTP status codes (201, 400, 401, 409, 500)
 * - Preventing duplicate entries
 * - Returning created resource with ID
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Validate ALL input fields before database insertion
 * - Use $1, $2 placeholders in SQL (NEVER string concatenation)
 * - Check for duplicate entries (email, username, etc.)
 * - Don't return sensitive data in response (passwords, tokens)
 * - Log errors server-side, don't expose details to client
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");
const db = require("../db/connection");

/**
 * POST /users - Create a new user
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * Request body:
 * {
 *   "email": "user@example.com",
 *   "username": "newuser",
 *   "password": "securepassword"
 * }
 *
 * Success Response (201):
 * {
 *   "data": {
 *     "id": 123,
 *     "email": "user@example.com",
 *     "username": "newuser",
 *     "created_at": "2024-01-15T10:30:00Z"
 *   }
 * }
 *
 * Error Responses:
 * - 400: Missing required fields or invalid input
 * - 401: Missing or invalid authentication token
 * - 409: User with email/username already exists
 * - 500: Server error
 */
router.post(
  "/users",
  authenticateToken, // Middleware: Verify JWT token before proceeding
  async (req, res) => {
    try {
      // Extract and validate required fields from request body
      const { email, username, password } = req.body;

      // Validate required fields are present
      if (!email || !username || !password) {
        return res.status(400).json({
          error: "Missing required fields",
          code: "MISSING_FIELDS",
          required: ["email", "username", "password"],
        });
      }

      // Validate email format (basic validation)
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        return res.status(400).json({
          error: "Invalid email format",
          code: "INVALID_EMAIL",
        });
      }

      // Validate password length (minimum 8 characters)
      if (password.length < 8) {
        return res.status(400).json({
          error: "Password must be at least 8 characters",
          code: "INVALID_PASSWORD",
        });
      }

      // Check if user with email already exists
      const existingUser = await db.query(
        "SELECT id FROM users WHERE email = $1 OR username = $2",
        [email, username]
      );

      if (existingUser.rows.length > 0) {
        return res.status(409).json({
          error: "User with this email or username already exists",
          code: "DUPLICATE_USER",
        });
      }

      // Insert new user into database using parameterized query
      // $1, $2, $3 are parameterized (prevents SQL injection)
      // Note: In production, password should be hashed with bcrypt
      const result = await db.query(
        "INSERT INTO users (email, username, password_hash, created_at) VALUES ($1, $2, $3, NOW()) RETURNING id, email, username, created_at",
        [email, username, password] // In production: use bcrypt.hash(password, 10)
      );

      const newUser = result.rows[0];

      // Return created user with 201 status
      // DO NOT return password or sensitive fields
      res.status(201).json({
        data: {
          id: newUser.id,
          email: newUser.email,
          username: newUser.username,
          created_at: newUser.created_at,
        },
      });
    } catch (error) {
      // Log full error server-side for debugging
      console.error("Error creating user:", error);

      // Return generic error to client (don't expose internal details)
      res.status(500).json({
        error: "Failed to create user",
        code: "CREATE_USER_ERROR",
      });
    }
  }
);

module.exports = router;

/**
 * USAGE EXAMPLE:
 *
 * // In your main server file (server.js or app.js):
 * const userRoutes = require('./routes/users');
 * app.use('/api', userRoutes);
 *
 * // Making a request from client:
 * fetch('/api/users', {
 *   method: 'POST',
 *   headers: {
 *     'Content-Type': 'application/json',
 *     'Authorization': 'Bearer <your_jwt_token>'
 *   },
 *   body: JSON.stringify({
 *     email: 'newuser@example.com',
 *     username: 'newuser',
 *     password: 'securepassword123'
 *   })
 * })
 * .then(res => res.json())
 * .then(data => {
 *   console.log(data.data);  // Created user object
 * });
 *
 * // Example success response:
 * {
 *   "data": {
 *     "id": 123,
 *     "email": "newuser@example.com",
 *     "username": "newuser",
 *     "created_at": "2024-01-15T10:30:00Z"
 *   }
 * }
 *
 * // Example error response (duplicate):
 * {
 *   "error": "User with this email or username already exists",
 *   "code": "DUPLICATE_USER"
 * }
 */