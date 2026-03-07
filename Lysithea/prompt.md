# Project Name
Book Store

# Stack
Frontend: React 18 + Tailwind
Backend: Express.js + Node 20
Database: PostgreSQL

# Features
- Books: crud
- Users: crud

# API Requirements
- Security: JWT
- Endpoint style: RESTful
- Validation: true
- Rate limiting: false

# Frontend Requirements
- Pages: Dashboard, Books, Login, Register

# Database / Schema Notes
- Tables:
  - books: title, author, price, stock_quantity, reserved_by_user_id
  - users: email, username, password_hash
- Relationships:
  - books has many users through reserved_by_user_id

# Extra Notes
- Use async/await throughout