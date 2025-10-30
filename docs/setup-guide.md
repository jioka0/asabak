# 🚀 NEKWASAR PORTFOLIO BACKEND SETUP GUIDE

## 📋 OVERVIEW
This guide will help you set up the complete backend system for NekwasaR's portfolio website, including:
- FastAPI backend with SQLite database
- JWT authentication for admin panel
- Contact form API integration
- Admin dashboard with email-like UI
- Production-ready security features

## 🛠️ PREREQUISITES
- Python 3.8+
- pip package manager
- Git (optional)

## 📦 INSTALLATION & SETUP

### 1. Install Dependencies
```bash
cd BACKEND
pip install -r requirements.txt
```

### 2. Database Setup
The database tables are created automatically when the server starts. No manual setup required.

### 3. Create Admin User
```bash
# Register first admin user
curl -X POST "http://127.0.0.1:8001/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@nekwasar.com",
    "password": "your_secure_password"
  }'
```

### 4. Start the Server
```bash
cd BACKEND
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

## 🔗 API ENDPOINTS

### Public Endpoints (No Auth Required)
- `POST /api/contacts/` - Submit contact form
- `GET /` - Redirect to portfolio site

### Admin Endpoints (JWT Auth Required)
- `POST /api/auth/login` - Admin login
- `GET /api/auth/me` - Get current user info
- `GET /api/contacts/` - Get all contact messages
- `GET /api/contacts/{id}` - Get specific contact
- `PUT /api/contacts/{id}/read` - Mark contact as read
- `DELETE /api/contacts/{id}` - Delete contact

### Admin Interface
- `GET /admin` - Admin login page
- `GET /admin/dashboard` - Admin dashboard (requires login)

## 🎯 TESTING THE SYSTEM

### 1. Test Contact Form Submission
```bash
curl -X POST "http://127.0.0.1:8001/api/contacts/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "Hello from API test!"
  }'
```

### 2. Test Admin Login
```bash
curl -X POST "http://127.0.0.1:8001/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password"
```

### 3. Test Protected Route (with token)
```bash
curl -X GET "http://127.0.0.1:8001/api/contacts/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🎨 ADMIN INTERFACE FEATURES

### Login Page (`/admin`)
- Clean, modern login form
- JWT token storage in localStorage
- Error handling and validation

### Dashboard (`/admin/dashboard`)
- Email-like message cards
- Read/unread status indicators
- Statistics bar (total, read, unread)
- Mark as read/unread functionality
- Delete messages
- Auto-refresh every 30 seconds
- Responsive design

## 🔒 SECURITY FEATURES

### Current (Development)
- JWT authentication with 30-minute tokens
- Password hashing with bcrypt
- Role-based access control
- CORS enabled for development

### Production Ready (Uncomment in main.py)
```python
# HTTPS Enforcement
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Enhanced CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])

# Enhanced Input Validation
# Uncomment the SecureContactCreate class in schemas.py
```

## 🚀 PRODUCTION DEPLOYMENT

### 1. Environment Variables
Create a `.env` file in the BACKEND directory:
```env
SECRET_KEY=your-production-secret-key
DATABASE_URL=sqlite:///./contacts.db
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. Update Configuration
- Change SECRET_KEY to a secure random string
- Update CORS_ORIGINS with your domain
- Set ALLOWED_HOSTS for your domain

### 3. Enable Production Security
Uncomment the security features in `main.py` as shown above.

### 4. Database Migration
For production, consider using PostgreSQL instead of SQLite:
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 5. Reverse Proxy (nginx example)
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 API DOCUMENTATION

Visit `http://127.0.0.1:8001/docs` for interactive API documentation with:
- All available endpoints
- Request/response examples
- Try-it-out functionality
- Schema definitions

## 🐛 TROUBLESHOOTING

### Common Issues:

1. **"Table doesn't exist" error**
   - Restart the server to create tables automatically

2. **CORS errors**
   - Check CORS_ORIGINS in production config

3. **Authentication fails**
   - Verify JWT token is valid and not expired
   - Check SECRET_KEY consistency

4. **Database connection issues**
   - Ensure SQLite file permissions
   - Check DATABASE_URL format

## 📞 SUPPORT

For issues or questions:
1. Check the API documentation at `/docs`
2. Review server logs for error details
3. Verify all dependencies are installed
4. Test with the provided curl commands

## 🎉 SUCCESS CHECKLIST

- [ ] Dependencies installed
- [ ] Server starts without errors
- [ ] Admin user created successfully
- [ ] Contact form submission works
- [ ] Admin login works
- [ ] Dashboard loads messages
- [ ] Security features enabled for production

## 📈 NEXT STEPS

1. **Test all functionality** with the provided commands
2. **Customize the admin UI** to match your branding
3. **Add more features** (blog posts, products, etc.)
4. **Deploy to production** with security enabled
5. **Set up monitoring** and backups

---

**🎯 Your portfolio backend is now ready for production!**