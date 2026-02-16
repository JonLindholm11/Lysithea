/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Update Query Function
 *
 * Updates a record by ID with new values
 * Returns the updated record
 */

const db = require('../../connection');

/**
 * Update user
 */
export async function updateUser(id, { email, username }) {
  const SQL = `
    UPDATE users
    SET email = $1, username = $2, updated_at = NOW()
    WHERE id = $3
    RETURNING *
  `;
  
  const { rows: [user] } = await db.query(SQL, [email, username, id]);
  
  if (!user) {
    throw new Error("User not found");
  }
  
  return user;
}