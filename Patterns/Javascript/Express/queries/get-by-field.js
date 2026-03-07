/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get By Field Query Function
 *
 * Retrieves a single record by a specific field value
 */

const db = require('../connection');

/**
 * Get user by email
 */
export async function getUserByEmail(email) {
  const SQL = `SELECT * FROM users WHERE email = $1`;
  const { rows } = await db.query(SQL, [email]);
  return rows[0];  //  Changed from 'return rows'
}