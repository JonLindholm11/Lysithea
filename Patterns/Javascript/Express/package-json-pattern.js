/**
 * @output-dir .
 * @file-naming package.json
 *
 * PATTERN: Node.js Package Manifest
 *
 * USE WHEN:
 * - Generating package.json for an Express + PostgreSQL project
 *
 * DEMONSTRATES:
 * - Core Express dependencies
 * - PostgreSQL client
 * - Auth and security packages
 * - Dev dependencies for development workflow
 */

{
  "name": "/* PROJECT_NAME */",
  "version": "1.0.0",
  "description": "",
  "main": "app.js",
  "scripts": {
    "start":   "node app.js",
    "dev":     "nodemon app.js",
    "seed":    "node db/seeds/run_seeds.js"
  },
  "dependencies": {
    "bcrypt":        "^5.1.1",
    "cors":          "^2.8.5",
    "dotenv":        "^16.4.5",
    "express":       "^4.18.3",
    "jsonwebtoken":  "^9.0.2",
    "pg":            "^8.11.3"
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}