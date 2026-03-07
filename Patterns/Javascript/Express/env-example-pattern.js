/**
 * @output-dir .
 * @file-naming .env.example
 *
 * PATTERN: Environment Variables Example
 *
 * USE WHEN:
 * - Generating environment variable template
 * - Documenting required config for new developers
 *
 * DEMONSTRATES:
 * - Database connection variables
 * - JWT secret
 * - Server port
 * - Node environment
 */

# Server
PORT=3000
NODE_ENV=development

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=/* PROJECT_NAME */
DB_USER=postgres
DB_PASSWORD=your_password_here

# JWT
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRES_IN=7d