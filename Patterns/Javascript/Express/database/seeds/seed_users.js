/**
 * @output-dir db/seeds
 * @file-naming {resource}.seed.js
 * 
 * PATTERN: Database Seed File
 *
 * USE WHEN:
 * - Populating tables with sample/test data
 * - Setting up development environment
 * - Creating demo data
 *
 * DEMONSTRATES:
 * - Async seeding with proper error handling
 * - Parameterized INSERT queries
 * - Sample data generation
 * - Console logging for feedback
 */

const db = require('../connection');

/**
 * Seed sample data for users table
 * 
 * Inserts realistic sample records for development/testing
 * Uses parameterized queries to prevent SQL injection
 */
async function seedUsers() {
  const users = [
    {
      email: 'john.doe@example.com',
      username: 'johndoe',
      password_hash: '$2b$10$abcdefghijklmnopqrstuvwxyz123456', // Example bcrypt hash
      created_at: new Date('2024-01-15'),
    },
    {
      email: 'jane.smith@example.com',
      username: 'janesmith',
      password_hash: '$2b$10$zyxwvutsrqponmlkjihgfedcba654321',
      created_at: new Date('2024-02-01'),
    },
    {
      email: 'bob.wilson@example.com',
      username: 'bobwilson',
      password_hash: '$2b$10$1234567890abcdefghijklmnopqrstuv',
      created_at: new Date('2024-03-10'),
    },
  ];

  for (const user of users) {
    await db.query(
      'INSERT INTO users (email, username, password_hash, created_at) VALUES ($1, $2, $3, $4)',
      [user.email, user.username, user.password_hash, user.created_at]
    );
  }

  console.log('✅ Seeded users');
}

module.exports = { seedUsers };