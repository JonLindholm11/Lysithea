// patterns/javascript/express/routes/delete-user-auth.js

/**
 * @output-dir api/routes
 * @file-naming {resource}.js
 * 
 * PATTERN: Express DELETE Route with Authentication
 *
 * USE WHEN:
 * - Deleting resources from database
 * - Route requires authentication (JWT)
 * - Using PostgreSQL with raw SQL queries
 * - Need to verify resource exists before deleting
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - URL parameter extraction (/:id)
 * - Parameterized SQL queries (SQL injection safe)
 * - Error handling with try/catch
 * - Proper HTTP status codes (200, 400, 401, 404, 500)
 * - Soft delete vs hard delete options
 * - Returning confirmation of deletion
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Use $1 placeholder in SQL (NEVER string concatenation)
 * - Validate ID is a number to prevent injection
 * - Check resource exists before attempting delete
 * - Consider soft delete (is_deleted flag) vs hard delete for data recovery
 * - Log errors server-side, don't expose details to client
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");
const db = require("../db/connection");

/**
 * DELETE /users/:id - Delete a user
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * URL parameters:
 * - id: User ID (integer)
 *
 * Success Response (200):
 * {
 *   "message": "User deleted successfully",
 *   "data": {
 *     "id": 123,
 *     "deleted_at": "2024-01-20T14:45:00Z"
 *   }
 * }
 *
 * Error Responses:
 * - 400: Invalid ID format
 * - 401: Missing or invalid authentication token
 * - 404: User not found
 * - 500: Server error
 */
router.delete(
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

      // Check if user exists before attempting to delete
      const existingUser = await db.query(
        "SELECT id FROM users WHERE id = $1",
        [userId],
      );

      if (existingUser.rows.length === 0) {
        return res.status(404).json({
          error: "User not found",
          code: "USER_NOT_FOUND",
        });
      }

      // OPTION 1: Soft delete (recommended for data recovery)
      // Sets is_deleted flag and deleted_at timestamp
      const result = await db.query(
        "UPDATE users SET is_deleted = true, deleted_at = NOW() WHERE id = $1 RETURNING id, deleted_at",
        [userId],
      );

      // OPTION 2: Hard delete (permanent removal)
      // Uncomment below and comment out above if you want hard delete
      // const result = await db.query(
      //   "DELETE FROM users WHERE id = $1 RETURNING id",
      //   [userId]
      // );

      const deletedUser = result.rows[0];

      // Return success confirmation
      res.status(200).json({
        message: "User deleted successfully",
        data: {
          id: deletedUser.id,
          deleted_at: deletedUser.deleted_at || new Date().toISOString(),
        },
      });
    } catch (error) {
      // Log full error server-side for debugging
      console.error("Error deleting user:", error);

      // Return generic error to client (don't expose internal details)
      res.status(500).json({
        error: "Failed to delete user",
        code: "DELETE_USER_ERROR",
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
 * fetch('/api/users/123', {
 *   method: 'DELETE',
 *   headers: {
 *     'Authorization': 'Bearer <your_jwt_token>'
 *   }
 * })
 * .then(res => res.json())
 * .then(data => {
 *   console.log(data.message);  // "User deleted successfully"
 * });
 *
 * // Example success response:
 * {
 *   "message": "User deleted successfully",
 *   "data": {
 *     "id": 123,
 *     "deleted_at": "2024-01-20T14:45:00Z"
 *   }
 * }
 *
 * // Example error response (not found):
 * {
 *   "error": "User not found",
 *   "code": "USER_NOT_FOUND"
 * }
 */
