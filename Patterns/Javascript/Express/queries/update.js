/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Update Query Function
 *
 * Updates a record by ID with partial field support.
 * Returns the updated record.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Build SET clause dynamically — only update fields provided in updates object
 * - Always append updated_at = NOW() to SET clause
 * - Do NOT hardcode email/username — adapt field names from schema
 * - Throw an error if record not found so route can return 404
 */

const db = require('../connection');

async function updateResource(id, updates) {
  const fields = [];
  const values = [];
  let paramCount = 1;

  // Dynamically build SET clause from provided fields
  for (const [key, value] of Object.entries(updates)) {
    if (value !== undefined) {
      fields.push(`${key} = $${paramCount}`);
      values.push(value);
      paramCount++;
    }
  }

  // Always update timestamp
  fields.push(`updated_at = NOW()`);

  // ID is the final parameter
  values.push(id);

  const SQL = `
    UPDATE resources
    SET ${fields.join(', ')}
    WHERE id = $${paramCount}
    RETURNING *
  `;

  const { rows: [record] } = await db.query(SQL, values);

  if (!record) {
    throw new Error("Resource not found");
  }

  return record;
}