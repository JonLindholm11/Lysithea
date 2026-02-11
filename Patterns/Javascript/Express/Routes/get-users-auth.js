// patterns/javascript/express/routes/get-users-auth.js

/**
 * @output-dir api/routes
 * @file-naming {resource}.js
 * 
 * PATTERN: Express GET Route with Authentication and Pagination
 *
 * USE WHEN:
 * - Fetching list of resources from database
 * - Route requires authentication (JWT)
 * - Need pagination for large datasets
 * - Using PostgreSQL with raw SQL queries
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - Pagination with page and limit parameters
 * - Parameterized SQL queries (SQL injection safe)
 * - Error handling with try/catch
 * - Proper HTTP status codes (200, 401, 500)
 * - Not exposing sensitive data (passwords, tokens)
 * - Pagination metadata in response
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Use $1, $2 placeholders in SQL (NEVER string concatenation)
 * - SELECT only non-sensitive fields (exclude password_hash, tokens)
 * - Cap maximum limit to prevent performance issues
 * - Log errors server-side, don't expose details to client
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");
const db = require("../db/connection");

/**
 * GET /users - Fetch all users with pagination
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * Query parameters:
 * - page: Page number (default: 1)
 * - limit: Results per page (default: 20, max: 100)
 *
 * Success Response (200):
 * {
 *   "data": [
 *     { "id": 1, "email": "user@example.com", "username": "user1", "created_at": "..." }
 *   ],
 *   "pagination": {
 *     "page": 1,
 *     "limit": 20,
 *     "total": 100,
 *     "totalPages": 5,
 *     "hasNext": true,
 *     "hasPrev": false
 *   }
 * }
 *
 * Error Responses:
 * - 401: Missing or invalid authentication token
 * - 500: Server error
 */
router.get(
  "/users",
  authenticateToken, // Middleware: Verify JWT token before proceeding
  async (req, res) => {
    try {
      // Extract and validate pagination parameters from query string
      const page = parseInt(req.query.page) || 1;

      // Cap limit at 100 to prevent performance issues
      const limit = Math.min(parseInt(req.query.limit) || 20, 100);

      // Calculate offset for SQL query
      const offset = (page - 1) * limit;

      // Fetch users from database using parameterized query
      // SELECT only non-sensitive fields (NO password_hash, reset_tokens, etc.)
      // $1, $2 are parameterized (prevents SQL injection)
      const users = await db.query(
        "SELECT id, email, username, created_at FROM users ORDER BY created_at DESC LIMIT $1 OFFSET $2",
        [limit, offset],
      );

      // Get total count of users for pagination metadata
      const countResult = await db.query("SELECT COUNT(*) as total FROM users");
      const total = parseInt(countResult.rows[0].total);

      // Calculate total pages
      const totalPages = Math.ceil(total / limit);

      // Return data with comprehensive pagination info
      res.status(200).json({
        data: users.rows,
        pagination: {
          page: page,
          limit: limit,
          total: total,
          totalPages: totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1,
        },
      });
    } catch (error) {
      // Log full error server-side for debugging
      console.error("Error fetching users:", error);

      // Return generic error to client (don't expose internal details)
      res.status(500).json({
        error: "Failed to fetch users",
        code: "FETCH_USERS_ERROR",
      });
    }
  },
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
 * fetch('/api/users?page=2&limit=10', {
 *   headers: {
 *     'Authorization': 'Bearer <your_jwt_token>'
 *   }
 * })
 * .then(res => res.json())
 * .then(data => {
 *   console.log(data.data);  // Array of users
 *   console.log(data.pagination);  // Pagination info
 * });
 *
 * // Example response:
 * {
 *   "data": [
 *     { "id": 11, "email": "user11@example.com", "username": "user11", "created_at": "2024-01-15T10:30:00Z" },
 *     { "id": 12, "email": "user12@example.com", "username": "user12", "created_at": "2024-01-14T15:20:00Z" },
 *     // ... 8 more users
 *   ],
 *   "pagination": {
 *     "page": 2,
 *     "limit": 10,
 *     "total": 100,
 *     "totalPages": 10,
 *     "hasNext": true,
 *     "hasPrev": true
 *   }
 * }
 */
