/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Get All Query Function
 *
 * Retrieves all records from a table with pagination.
 * Returns { data, total } — generic key so routes work for any resource.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Return { data: rows, total } — never { users } or { posts }
 * - Do NOT use SELECT * — list explicit columns from schema
 * - Exclude password_hash from SELECT
 */

const db = require('../connection');

async function getResources(page = 1, limit = 20) {
  const offset = (page - 1) * limit;

  const SQL = `
    SELECT id, name, created_at, updated_at
    FROM resources
    ORDER BY created_at DESC
    LIMIT $1 OFFSET $2
  `;

  const { rows: data } = await db.query(SQL, [limit, offset]);

  const countSQL = `SELECT COUNT(*) AS total FROM resources WHERE is_deleted = FALSE`;
  const { rows: [{ total }] } = await db.query(countSQL);

  return {
    data,
    total: parseInt(total),
  };
}