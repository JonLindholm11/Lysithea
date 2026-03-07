// patterns/javascript/express/routes/get-users-auth.js

/**
 * @output-dir api/routes
 * @file-naming {resource}.js
 *
 * PATTERN: Express GET All Route with Authentication and Pagination
 *
 * USE WHEN:
 * - Fetching list of resources from database
 * - Route requires authentication (JWT)
 * - Need pagination for large datasets
 *
 * DEMONSTRATES:
 * - JWT authentication middleware
 * - Pagination with page and limit parameters
 * - Error handling with try/catch
 * - Proper HTTP status codes (200, 401, 500)
 * - Pagination metadata in response
 *
 * SECURITY NOTES:
 * - authenticateToken middleware REQUIRED for protected routes
 * - Cap maximum limit to prevent performance issues
 * - Log errors server-side, don't expose details to client
 */

const express = require("express");
const router = express.Router();
const { authenticateToken } = require("../middleware/auth");

/**
 * GET / - Fetch all resources with pagination
 *
 * Authentication: Required (JWT token in Authorization header)
 *
 * Query parameters:
 * - page:  Page number (default: 1)
 * - limit: Results per page (default: 20, max: 100)
 *
 * Success Response (200):
 * {
 *   "data": [ { "id": 1, ...fields } ],
 *   "pagination": {
 *     "page": 1, "limit": 20, "total": 100,
 *     "totalPages": 5, "hasNext": true, "hasPrev": false
 *   }
 * }
 */
router.get(
  "/",
  authenticateToken,
  async (req, res) => {
    try {
      const page  = parseInt(req.query.page)  || 1;
      const limit = Math.min(parseInt(req.query.limit) || 20, 100);

      // Call the get-all query function — it returns { data, total }
      const result     = await getResources(page, limit);
      const items      = result.data  ?? result[Object.keys(result)[0]];
      const total      = result.total ?? 0;
      const totalPages = Math.ceil(total / limit);

      res.status(200).json({
        data: items,
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
      console.error("Error fetching resources:", error);
      res.status(500).json({
        error: "Failed to fetch resources",
        code:  "FETCH_ERROR",
      });
    }
  }
);

module.exports = router;