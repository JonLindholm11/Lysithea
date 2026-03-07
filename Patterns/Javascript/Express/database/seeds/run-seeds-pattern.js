/**
 * @output-dir db/seeds
 * @file-naming run_seeds.js
 *
 * PATTERN: Seed Runner
 *
 * USE WHEN:
 * - Running all seed files in sequence
 * - Setting up development database
 *
 * DEMONSTRATES:
 * - Importing and calling all seed functions
 * - Sequential async execution
 * - Error handling
 * - Closing db connection after seeding
 */

const db = require('../connection');

/* IMPORTS */

async function runAllSeeds() {
  console.log('🌱 Running seeds...\n');
  try {
/* CALLS */
    console.log('\n✅ All seeds complete');
  } catch (error) {
    console.error('❌ Seed failed:', error);
    process.exit(1);
  } finally {
    await db.end();
  }
}

runAllSeeds();