// patterns/javascript/express/routes/put-user-auth.js

/**
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
const db = require("../db/connection");

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

      // Extract fields from request body
      const { email, username } = req.body;

      // Validate at least one field is provided for update
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
      const existingUser = await db.query(
        "SELECT id FROM users WHERE id = $1",
        [userId]
      );

      if (existingUser.rows.length === 0) {
        return res.status(404).json({
          error: "User not found",
          code: "USER_NOT_FOUND",
        });
      }

      // Check if email/username is already taken by another user
      if (email || username) {
        const duplicateCheck = await db.query(
          "SELECT id FROM users WHERE (email = $1 OR username = $2) AND id != $3",
          [email || "", username || "", userId]
        );

        if (duplicateCheck.rows.length > 0) {
          return res.status(409).json({
            error: "Email or username already taken",
            code: "DUPLICATE_USER",
          });
        }
      }

      // Build dynamic UPDATE query based on provided fields
      const updates = [];
      const values = [];
      let paramCount = 1;

      if (email) {
        updates.push(`email = $${paramCount}`);
        values.push(email);
        paramCount++;
      }

      if (username) {
        updates.push(`username = $${paramCount}`);
        values.push(username);
        paramCount++;
      }

      // Add updated_at timestamp
      updates.push(`updated_at = NOW()`);

      // Add user ID as final parameter
      values.push(userId);

      // Execute update query
      // $1, $2, etc. are parameterized (prevents SQL injection)
      const result = await db.query(
        `UPDATE users SET ${updates.join(", ")} WHERE id = $${paramCount} RETURNING id, email, username, created_at, updated_at`,
        values
      );

      const updatedUser = result.rows[0];

      // Return updated user with 200 status
      // DO NOT return password or sensitive fields
      res.status(200).json({
        data: updatedUser,
      });
    } catch (error) {
      // Log full error server-side for debugging
      console.error("Error updating user:", error);

      // Return generic error to client (don't expose internal details)
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