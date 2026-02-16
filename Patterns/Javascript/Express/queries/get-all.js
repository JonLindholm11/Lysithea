/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Get All Query Function
 *
 * Retrieves all records from a table
 */

const db = require('../../connection');

/**
 * Get all users
 */
export async function getUsers() {
  const SQL = `SELECT * FROM users`;
  const { rows: users } = await db.query(SQL);
  return users;
}