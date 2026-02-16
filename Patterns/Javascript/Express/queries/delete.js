/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Delete Query Function
 *
 * Soft delete - marks record as deleted
 */

const db = require('../../connection');

/**
 * Delete user (soft delete)
 */
export async function deleteUser(id) {
  const SQL = `
    UPDATE users
    SET is_deleted = true, deleted_at = NOW()
    WHERE id = $1
    RETURNING id
  `;
  
  const { rows: [deleted] } = await db.query(SQL, [id]);
  
  if (!deleted) {
    throw new Error("User not found");
  }
  
  return deleted;
}