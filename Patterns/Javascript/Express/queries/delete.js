/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Delete Query Function
 *
 * Soft-deletes a record by setting is_deleted = true.
 * Returns the deleted record's id and deleted_at.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Soft delete only — set is_deleted = true, deleted_at = NOW()
 * - Return id so route can confirm deletion
 * - Throw an error if record not found so route can return 404
 */

const db = require('../connection');

async function deleteResource(id) {
  const SQL = `
    UPDATE resources
    SET is_deleted = true, deleted_at = NOW()
    WHERE id = $1
    RETURNING id, deleted_at
  `;

  const { rows: [deleted] } = await db.query(SQL, [id]);

  if (!deleted) {
    throw new Error("Resource not found");
  }

  return deleted;
}