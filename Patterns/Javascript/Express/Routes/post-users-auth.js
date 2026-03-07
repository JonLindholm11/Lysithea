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
 * - Need input validation
 * - Using PostgreSQL via query functions
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - Request body validation
 * - Error handling with try/catch
 * - Proper HTTP status codes (201, 400, 500)
 * - Returning created resource
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Validate ALL input fields before database insertion
 * - Do NOT hash passwords here — password hashing belongs in auth routes only
 * - Do NOT call getUserByEmail or any auth-specific functions here
 * - Do NOT import bcrypt — this is a generic resource route, not an auth route
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");

/**
 * POST / - Create a new resource
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * Request body: resource fields from schema
 *
 * Success Response (201):
 * { "data": { "id": 123, ...fields, "created_at": "..." } }
 *
 * Error Responses:
 * - 400: Missing required fields
 * - 401: Missing or invalid authentication token
 * - 500: Server error
 */
router.post(
  "/",
  authenticateToken,
  async (req, res) => {
    try {
      const fields = req.body;

      // Validate required fields exist
      if (!fields || Object.keys(fields).length === 0) {
        return res.status(400).json({
          error: "Missing required fields",
          code: "MISSING_FIELDS",
        });
      }

      // Create resource using the imported query function
      const newRecord = await createResource(fields);

      res.status(201).json({ data: newRecord });
    } catch (error) {
      console.error("Error creating resource:", error);

      res.status(500).json({
        error: "Failed to create resource",
        code: "CREATE_ERROR",
      });
    }
  }
);

module.exports = router;