/**
 * @output-dir .
 * @file-naming README.md
 *
 * PATTERN: Project README
 *
 * USE WHEN:
 * - Generating per-project README
 */

# /* PROJECT_NAME */

## Setup

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment
```bash
cp .env.example .env
```
Edit `.env` with your database credentials and JWT secret.

### 3. Set up the database
```bash
psql -U postgres -c "CREATE DATABASE /* DB_NAME */;"
psql -U postgres -d /* DB_NAME */ -f db/schema.sql
```

### 4. Seed the database
```bash
npm run seed
```

### 5. Start the server
```bash
# Development
npm run dev

# Production
npm start
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register a new user |
| POST | /api/auth/login | Login and get JWT token |

/* ENDPOINTS */

## Environment Variables

| Variable | Description |
|----------|-------------|
| PORT | Server port (default: 3000) |
| NODE_ENV | Environment (development/production) |
| DB_HOST | Database host |
| DB_PORT | Database port |
| DB_NAME | Database name |
| DB_USER | Database user |
| DB_PASSWORD | Database password |
| JWT_SECRET | Secret key for JWT signing |
| JWT_EXPIRES_IN | JWT expiry duration (default: 7d) |