// patterns/javascript/express/routes/put-user-auth.js

/**
 * @output-dir api/routes
 * @file-naming {resource}.js

 * PATTERN: Express PUT Route with Authentication and Validation
 *
 * USE WHEN:
 * - Updating existing resources in database
 * - Route requires authentication (JWT)
 * - Need input validation and sanitization
 * - Using PostgreSQL with raw SQL queries
 * - Need to verify resource exists before updating
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - URL parameter extraction (/:id)
 * - Request body validation
 * - Parameterized SQL queries (SQL injection safe)
 * - Error handling with try/catch
 * - Proper HTTP status codes (200, 400, 401, 404, 409, 500)
 * - Preventing duplicate entries
 * - Returning updated resource
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Validate ALL input fields before database update
 * - Use $1, $2 placeholders in SQL (NEVER string concatenation)
 * - Check resource exists before attempting update
 * - Check for duplicate entries on unique fields
 * - Don't return sensitive data in response (passwords, tokens)
 * - Log errors server-side, don't expose details to client
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");

/**
 * PUT /users/:id - Update an existing user
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * URL parameters:
 * - id: User ID (integer)
 *
 * Request body:
 * {
 *   "email": "newemail@example.com",
 *   "username": "newusername"
 * }
 *
 * Success Response (200):
 * {
 *   "data": {
 *     "id": 123,
 *     "email": "newemail@example.com",
 *     "username": "newusername",
 *     "created_at": "2024-01-15T10:30:00Z",
 *     "updated_at": "2024-01-20T14:45:00Z"
 *   }
 * }
 *
 * Error Responses:
 * - 400: Invalid ID format or missing required fields
 * - 401: Missing or invalid authentication token
 * - 404: User not found
 * - 409: Email/username already taken by another user
 * - 500: Server error
 */
router.put(
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

      const { email, username } = req.body;

      // Validate at least one field provided
      if (!email && !username) {
        return res.status(400).json({
          error: "At least one field required for update",
          code: "MISSING_UPDATE_FIELDS",
          allowed: ["email", "username"],
        });
      }

      // Validate email format if provided
      if (email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
          return res.status(400).json({
            error: "Invalid email format",
            code: "INVALID_EMAIL",
          });
        }
      }


      // Check if user exists
      const existingUser = await getUserById(userId);
      
      if (!existingUser) {
        return res.status(404).json({
          error: "User not found",
          code: "USER_NOT_FOUND",
        });
      }

      // Check for duplicate email (if changing email)
      if (email && email !== existingUser.email) {
        const duplicate = await getUserByEmail(email);
        if (duplicate && duplicate.id !== userId) {
          return res.status(409).json({
            error: "Email already taken",
            code: "DUPLICATE_EMAIL",
          });
        }
      }

      // Update user
      const updatedUser = await updateUser(userId, { email, username });

      // Don't return password_hash
      delete updatedUser.password_hash;

      res.status(200).json({
        data: updatedUser,
      });
    } catch (error) {
      console.error("Error updating user:", error);

      res.status(500).json({
        error: "Failed to update user",
        code: "UPDATE_USER_ERROR",
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
 *   method: 'PUT',
 *   headers: {
 *     'Content-Type': 'application/json',
 *     'Authorization': 'Bearer <your_jwt_token>'
 *   },
 *   body: JSON.stringify({
 *     email: 'newemail@example.com',
 *     username: 'newusername'
 *   })
 * })
 * .then(res => res.json())
 * .then(data => {
 *   console.log(data.data);  // Updated user object
 * });
 *
 * // Example success response:
 * {
 *   "data": {
 *     "id": 123,
 *     "email": "newemail@example.com",
 *     "username": "newusername",
 *     "created_at": "2024-01-15T10:30:00Z",
 *     "updated_at": "2024-01-20T14:45:00Z"
 *   }
 * }
 *
 * // Example error response (duplicate):
 * {
 *   "error": "Email or username already taken",
 *   "code": "DUPLICATE_USER"
 * }
 */