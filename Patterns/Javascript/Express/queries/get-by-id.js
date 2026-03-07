/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Get By ID Query Function
 *
 * Retrieves a single record by primary key.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Do NOT use SELECT * — list explicit columns from schema
 * - Exclude password_hash from SELECT
 */

const db = require('../connection');

async function getResourceById(id) {
  const SQL = `
    SELECT id, name, created_at, updated_at
    FROM resources
    WHERE id = $1
  `;
  const { rows } = await db.query(SQL, [id]);
  return rows[0];
}