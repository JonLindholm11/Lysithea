/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get By ID Query Function
 *
 * Retrieves a single record by primary key
 */

const db = require('../../connection');

/**
 * Get user by ID
 */
export async function getUserById(id) {
  const SQL = `SELECT * FROM users WHERE id = $1`;
  const { rows } = await db.query(SQL, [id]);
  return rows[0];
}