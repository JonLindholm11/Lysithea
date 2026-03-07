# Project Name
Blog

# Stack
Frontend: React 18 + Tailwind
Backend: Express.js + Node 20
Database: PostgreSQL

# Features
- Users: crud
- Posts: crud

# API Requirements
- Security: JWT
- Endpoint style: RESTful
- Validation: true
- Rate limiting: false

# Frontend Requirements
- Users: dashboard
- Posts: dashboard, form

# Database / Schema Notes
- Tables:
  - users: email, username, password_hash
  - posts: title, content, user_id
- Relationships:
  - posts has many users

# Extra Notes
- Use async/await throughout
- Style: corporate