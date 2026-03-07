// patterns/javascript/express/routes/put-users-auth.js

/**
 * @output-dir api/routes
 * @file-naming {resource}.js
 *
 * PATTERN: Express PUT Route with Authentication and Validation
 *
 * USE WHEN:
 * - Updating existing resources in database
 * - Route requires authentication (JWT)
 * - Need input validation
 * - Using PostgreSQL via query functions
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - URL parameter extraction (/:id)
 * - Request body validation
 * - Error handling with try/catch
 * - Proper HTTP status codes (200, 400, 401, 404, 500)
 * - Returning updated resource
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Validate ALL input fields before database update
 * - Do NOT call getUserByEmail or any auth-specific functions here
 * - Do NOT import bcrypt — this is a generic resource route, not an auth route
 * - Check resource exists before attempting update
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");

/**
 * PUT /:id - Update an existing resource
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * URL parameters:
 * - id: Resource ID (integer)
 *
 * Request body: fields to update
 *
 * Success Response (200):
 * { "data": { "id": 123, ...fields, "updated_at": "..." } }
 *
 * Error Responses:
 * - 400: Invalid ID format or missing fields
 * - 401: Missing or invalid authentication token
 * - 404: Resource not found
 * - 500: Server error
 */
router.put(
  "/:id",
  authenticateToken,
  async (req, res) => {
    try {
      const resourceId = parseInt(req.params.id);

      if (isNaN(resourceId)) {
        return res.status(400).json({
          error: "Invalid ID format",
          code: "INVALID_ID",
        });
      }

      const updates = req.body;

      if (!updates || Object.keys(updates).length === 0) {
        return res.status(400).json({
          error: "At least one field required for update",
          code: "MISSING_UPDATE_FIELDS",
        });
      }

      // Check if resource exists
      const existing = await getResourceById(resourceId);

      if (!existing) {
        return res.status(404).json({
          error: "Resource not found",
          code: "NOT_FOUND",
        });
      }

      // Update resource
      const updated = await updateResource(resourceId, updates);

      res.status(200).json({ data: updated });
    } catch (error) {
      console.error("Error updating resource:", error);

      res.status(500).json({
        error: "Failed to update resource",
        code: "UPDATE_ERROR",
      });
    }
  }
);

module.exports = router;