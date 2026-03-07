/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 *
 * PATTERN: Create Query Function
 *
 * Inserts a new record and returns it.
 *
 * CRITICAL:
 * - Use CommonJS: async function, NO export keyword
 * - Accept a plain object of field values from req.body
 * - Use RETURNING * so the full record is returned to the route
 * - Do NOT hardcode users/email/username — adapt column names from schema
 * - Do NOT hash passwords here — password hashing is auth.js only
 */

const db = require('../connection');

async function createResource({ field1, field2 }) {
  const SQL = `
    INSERT INTO resources (field1, field2, created_at)
    VALUES ($1, $2, NOW())
    RETURNING *
  `;

  const values = [field1, field2];
  const { rows: [record] } = await db.query(SQL, values);
  return record;
}