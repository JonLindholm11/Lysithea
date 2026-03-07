/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Update Query Function
 *
 * Updates a record by ID with new values
 * Returns the updated record
 */

const db = require('../connection');

/**
 * Update user (supports partial updates)
 */
export async function updateUser(id, updates) {
  // Build dynamic query based on provided fields
  const fields = [];
  const values = [];
  let paramCount = 1;

  if (updates.email !== undefined) {
    fields.push(`email = $${paramCount}`);
    values.push(updates.email);
    paramCount++;
  }

  if (updates.username !== undefined) {
    fields.push(`username = $${paramCount}`);
    values.push(updates.username);
    paramCount++;
  }

  // Always update timestamp
  fields.push(`updated_at = NOW()`);

  // Add ID as final parameter
  values.push(id);

  const SQL = `
    UPDATE users
    SET ${fields.join(', ')}
    WHERE id = $${paramCount}
    RETURNING *
  `;
  
  const { rows: [user] } = await db.query(SQL, values);
  
  if (!user) {
    throw new Error("User not found");
  }
  
  return user;
}