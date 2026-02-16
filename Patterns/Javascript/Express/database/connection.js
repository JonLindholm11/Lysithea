/**
 * @output-dir db
 * @file-naming connection.js
 * 
 * PATTERN: PostgreSQL Database Connection
 *
 * USE WHEN:
 * - Setting up database connection pool
 * - Connecting to PostgreSQL database
 * - Using environment variables for config
 */

const { Pool } = require('pg');

// Create connection pool
const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'myapp',
  password: process.env.DB_PASSWORD || 'password',
  port: process.env.DB_PORT || 5432,
  max: 20, // Maximum number of clients in pool
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test connection on startup
pool.on('connect', () => {
  console.log('Connected to PostgreSQL database');
});

pool.on('error', (err) => {
  console.error('Unexpected database error:', err);
  process.exit(-1);
});

module.exports = pool;