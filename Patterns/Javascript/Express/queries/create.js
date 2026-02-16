/**
 * @output-dir db/queries
 * @file-naming {resource}.queries.js
 * 
 * PATTERN: Create Query Function
 */

const db = require('../../connection');

/**
 * Create a new user
 */
export async function createUser({ email, username, password_hash }) {
  const SQL = `
    INSERT INTO users (email, username, password_hash, created_at)
    VALUES ($1, $2, $3, NOW())
    RETURNING *
  `;
  
  const values = [email, username, password_hash];
  const { rows: [user] } = await db.query(SQL, values);
  return user;
}