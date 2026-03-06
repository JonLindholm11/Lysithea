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
  authenticateToken,
  async (req, res) => {
    try {
      const { id } = req.params;
      const userId = parseInt(id);

      if (isNaN(userId)) {
        return res.status(400).json({
          error: "Invalid user ID format",
          code: "INVALID_ID",
        });
      }

      // Delete user (soft delete - handles existence check internally)
      const deletedUser = await deleteUser(userId);  //  Use userId, returns deleted user

      // Return success
      res.status(200).json({
        message: "User deleted successfully",
        data: {
          id: deletedUser.id,
          deleted_at: deletedUser.deleted_at || new Date().toISOString(),
        },
      });
    } catch (error) {
      // Check if error is "User not found"
      if (error.message === "User not found") {
        return res.status(404).json({
          error: "User not found",
          code: "USER_NOT_FOUND",
        });
      }

      console.error("Error deleting user:", error);

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
