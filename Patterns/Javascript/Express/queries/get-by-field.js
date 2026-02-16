/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get By Field Query Function
 *
 * Retrieves records by a specific field value
 */

const db = require('../../connection');

/**
 * Get users by email
 */
export async function getUsersByEmail(email) {
  const SQL = `SELECT * FROM users WHERE email = $1`;
  const { rows } = await db.query(SQL, [email]);
  return rows;
}