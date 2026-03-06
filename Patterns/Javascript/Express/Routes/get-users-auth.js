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
  authenticateToken,
  async (req, res) => {
    try {
      // Extract and validate pagination parameters
      const page = parseInt(req.query.page) || 1;
      const limit = Math.min(parseInt(req.query.limit) || 20, 100);
      const offset = (page - 1) * limit;


      const { users, total } = await getUsers(page, limit);  //  Destructure

      const totalPages = Math.ceil(total / limit);

      res.status(200).json({
        data: users,  //  Clean!
        pagination: {
          page,
          limit,
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1,
        },
      });
    } catch (error) {
      console.error("Error fetching users:", error);

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
