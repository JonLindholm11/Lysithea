/**
 * @output-dir api/middleware
 * @file-naming auth.js
 * 
 * PATTERN: JWT Authentication Middleware
 *
 * USE WHEN:
 * - Protecting routes with JWT authentication
 * - Verifying tokens from Authorization header
 * - Adding user data to request object
 *
 * DEMONSTRATES:
 * - JWT token verification
 * - Bearer token extraction
 * - Error handling for invalid/missing tokens
 * - Adding decoded user to req.user
 */

const jwt = require("jsonwebtoken");

/**
 * Middleware to authenticate JWT tokens
 * 
 * Expects Authorization header: "Bearer <token>"
 * Adds decoded user to req.user if valid
 * Returns 401 if token is missing or invalid
 */
function authenticateToken(req, res, next) {
  // Extract token from Authorization header
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({
      error: "Authentication required",
      code: "MISSING_TOKEN"
    });
  }

  try {
    // Verify token with secret from environment variable
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Add user data to request object for downstream use
    req.user = decoded;
    
    // Continue to next middleware/route handler
    next();
  } catch (error) {
    // Token is invalid or expired
    return res.status(403).json({
      error: "Invalid or expired token",
      code: "INVALID_TOKEN"
    });
  }
}

module.exports = { authenticateToken };