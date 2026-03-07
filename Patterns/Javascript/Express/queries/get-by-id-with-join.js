/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Get By ID With Join Query Function
 *
 * Retrieves a single record by ID with related data via LEFT JOINs.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Build JOIN for every REFERENCES column in the schema
 * - Alias joined columns to avoid name collisions (e.g. related_table.name AS related_name)
 * - Exclude password_hash from all SELECT clauses
 */

const db = require('../connection');

async function getResourceByIdWithDetails(id) {
  const SQL = `
    SELECT
      resources.id,
      resources.field1,
      resources.field2,
      resources.created_at,
      related.id   AS related_id,
      related.name AS related_name
    FROM resources
    LEFT JOIN related ON resources.related_id = related.id
    WHERE resources.id = $1
  `;
  const { rows } = await db.query(SQL, [id]);
  return rows[0];
}