# 🛠️ NekwasaR Platform Setup Guide

This guide ensures a smooth installation and deployment process for the NekwasaR ecosystem.

## 📋 System Requirements
- **Python**: 3.10+ (Tested on 3.13)
- **Database**: PostgreSQL (Recommended) or SQLite
- **Environment**: Linux/macOS/Windows (WSL2 recommended)

---

## 🏗️ Backend Installation

### 1. Environment Preparation
Create and activate a virtual environment:
```bash
cd BACKEND
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Dependency Management
Install the core engine and its dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration (`.env`)
Create a `.env` file in the root directory (or use your host's environment variables):
```env
DATABASE_URL=postgresql://user:password@localhost/nekwasar_db
SECRET_KEY=generate-a-secure-random-string
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Database Initialization
The system uses SQLAlchemy to automatically manage its schema. On the first run, all tables (including `blog_views`, `blog_likes`, and `blog_comments`) will be created:
```bash
# From the root of the project
cd BACKEND/app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔐 Admin Access

To access the Admin Dashboard (`/admin`), you must register an initial administrative user:

```bash
# Register via API (One-time)
curl -X POST "http://127.0.0.1:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@nekwasar.com",
    "password": "your_secure_password"
  }'
```

---

## 📊 Engagement System Features

The platform uses a sophisticated **Unique Engagement System** to prevent artificial stats:

### Unique View Tracking (24h Cooldown)
- **Mechanic**: Uses browser fingerprinting + Session storage.
- **Verification**: Backend checks the `blog_views` table for matching fingerprints within a 24-hour window before incrementing the count.
- **Behavior**: Normal page reloads do not trigger additional views.

### Verified Likes & Comments
- **Anonymity**: Supports anonymous comments via device ID fingerprinting.
- **Persistence**: Likes are stored with a 3-day expiration period for non-logged-in users.

---

## 🐳 Docker Deployment

For production deployments using Docker:

1.  **Build & Scale**:
    ```bash
    docker-compose up -d --build
    ```
2.  **Volumes**: Ensure the database volume is mapped if using SQLite, or use a managed PostgreSQL service.
3.  **Reverse Proxy**: Use the provided `nginx.conf` to handle subdomain routing (iam. | blog. | store.).

---

## 🛠️ Troubleshooting

- **ImportError: ViewCreate**: Ensure you have removed the old flat `schemas.py` and are using the modular `schemas/` directory.
- **Database Connection**: Verify your `DATABASE_URL` format. PostgreSQL requires `psycopg2-binary`.
- **Stat Persistence**: If views are not updating, clear your `sessionStorage` in the browser dev tools for testing.

---
*Updated: January 1, 2026*