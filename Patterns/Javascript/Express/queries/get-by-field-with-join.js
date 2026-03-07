/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Get By Field With Join Query Function
 *
 * Retrieves multiple records by a field value with related data via LEFT JOINs.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Build JOIN for every REFERENCES column in the schema
 * - Alias joined columns to avoid name collisions
 * - Exclude password_hash from all SELECT clauses
 * - Returns an array (multiple rows), not a single row
 */

const db = require('../connection');

async function getResourcesByFieldWithDetails(fieldValue) {
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
    WHERE resources.field = $1
  `;
  const { rows } = await db.query(SQL, [fieldValue]);
  return rows;
}