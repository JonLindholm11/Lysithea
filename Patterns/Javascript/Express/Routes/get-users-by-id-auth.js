// patterns/javascript/express/routes/get-user-by-id-auth.js

/**
 * PATTERN: Express GET by ID Route with Authentication
 *
 * USE WHEN:
 * - Fetching single resource by ID from database
 * - Route requires authentication (JWT)
 * - Using PostgreSQL with raw SQL queries
 * - Need to handle "not found" cases
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - URL parameter extraction (/:id)
 * - Parameterized SQL queries (SQL injection safe)
 * - Error handling with try/catch
 * - Proper HTTP status codes (200, 401, 404, 500)
 * - Not exposing sensitive data (passwords, tokens)
 * - Handling resource not found
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Use $1 placeholder in SQL (NEVER string concatenation)
 * - SELECT only non-sensitive fields (exclude password_hash, tokens)
 * - Validate ID is a number to prevent injection
 * - Log errors server-side, don't expose details to client
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");
const db = require("../db/connection");

/**
 * GET /users/:id - Fetch single user by ID
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * URL parameters:
 * - id: User ID (integer)
 *
 * Success Response (200):
 * {
 *   "data": {
 *     "id": 1,
 *     "email": "user@example.com",
 *     "username": "user1",
 *     "created_at": "2024-01-15T10:30:00Z"
 *   }
 * }
 *
 * Error Responses:
 * - 400: Invalid ID format
 * - 401: Missing or invalid authentication token
 * - 404: User not found
 * - 500: Server error
 */
router.get(
  "/users/:id",
  authenticateToken, // Middleware: Verify JWT token before proceeding
  async (req, res) => {
    try {
      // Extract and validate ID from URL parameters
      const { id } = req.params;
      const userId = parseInt(id);

      // Validate ID is a valid number
      if (isNaN(userId)) {
        return res.status(400).json({
          error: "Invalid user ID format",
          code: "INVALID_ID",
        });
      }

      // Fetch user from database using parameterized query
      // SELECT only non-sensitive fields (NO password_hash, reset_tokens, etc.)
      // $1 is parameterized (prevents SQL injection)
      const result = await db.query(
        "SELECT id, email, username, created_at FROM users WHERE id = $1",
        [userId]
      );

      // Check if user was found
      if (result.rows.length === 0) {
        return res.status(404).json({
          error: "User not found",
          code: "USER_NOT_FOUND",
        });
      }

      const user = result.rows[0];

      // Return user data
      res.status(200).json({
        data: user,
      });
    } catch (error) {
      // Log full error server-side for debugging
      console.error("Error fetching user:", error);

      // Return generic error to client (don't expose internal details)
      res.status(500).json({
        error: "Failed to fetch user",
        code: "FETCH_USER_ERROR",
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
 * fetch('/api/users/123', {
 *   headers: {
 *     'Authorization': 'Bearer <your_jwt_token>'
 *   }
 * })
 * .then(res => res.json())
 * .then(data => {
 *   console.log(data.data);  // User object
 * });
 *
 * // Example success response:
 * {
 *   "data": {
 *     "id": 123,
 *     "email": "user@example.com",
 *     "username": "user123",
 *     "created_at": "2024-01-15T10:30:00Z"
 *   }
 * }
 *
 * // Example error response (not found):
 * {
 *   "error": "User not found",
 *   "code": "USER_NOT_FOUND"
 * }
 */