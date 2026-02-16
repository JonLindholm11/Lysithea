/**
 * @output-dir db
 * @file-naming schema.sql
 * 
 * PATTERN: PostgreSQL Table Schema
 *
 * USE WHEN:
 * - Creating database tables
 * - Defining table structure
 * - Setting up constraints and indexes
 */

-- Table: {resource}
CREATE TABLE IF NOT EXISTS {resource} (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(10, 2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP,
  is_deleted BOOLEAN DEFAULT FALSE,
  deleted_at TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_{resource}_name ON {resource}(name);
CREATE INDEX IF NOT EXISTS idx_{resource}_created_at ON {resource}(created_at);
CREATE INDEX IF NOT EXISTS idx_{resource}_is_deleted ON {resource}(is_deleted);