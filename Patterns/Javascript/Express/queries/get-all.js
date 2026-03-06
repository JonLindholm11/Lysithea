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
 * Get all users with pagination
 */
export async function getUsers(page = 1, limit = 20) {
  const offset = (page - 1) * limit;
  
  const SQL = `
    SELECT * FROM users 
    ORDER BY created_at DESC 
    LIMIT $1 OFFSET $2
  `;
  
  const { rows: users } = await db.query(SQL, [limit, offset]);
  
  // Get total count for pagination
  const countSQL = `SELECT COUNT(*) as total FROM users`;
  const { rows: [{ total }] } = await db.query(countSQL);
  
  return {
    users,
    total: parseInt(total),
  };
}