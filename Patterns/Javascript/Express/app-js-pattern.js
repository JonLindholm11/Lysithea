/**
 * @output-dir .
 * @file-naming app.js
 *
 * PATTERN: Express App Entry Point
 *
 * USE WHEN:
 * - Generating the main server file
 * - Mounting all resource routes
 * - Connecting middleware
 *
 * DEMONSTRATES:
 * - Express app setup
 * - dotenv config
 * - JSON body parsing
 * - CORS middleware
 * - Route mounting
 * - Server startup with port from env
 */

const express = require('express');
const cors    = require('cors');
require('dotenv').config();

const app = express();

// ─── Middleware ───────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ─── Routes ───────────────────────────────────────────────────────────────────
/* IMPORTS */
/* ROUTES */

// ─── Health check ─────────────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// ─── Global error handler ─────────────────────────────────────────────────────
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal server error',
    code:  'INTERNAL_ERROR',
  });
});

// ─── Start server ─────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;