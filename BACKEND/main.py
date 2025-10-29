from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from database import create_tables
from routes import contacts, blogs, products, auth

# Create FastAPI app
app = FastAPI(
    title="NekwasaR Portfolio API",
    description="Backend API for NekwasaR's portfolio website",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(blogs.router, prefix="/api/blogs", tags=["blogs"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# Mount static files for admin interface
app.mount("/static", StaticFiles(directory="../STATIC"), name="static")

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    create_tables()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to main portfolio site"""
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=http://127.0.0.1:8000" />
        </head>
        <body>
            <p>Redirecting to portfolio site...</p>
        </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
async def admin_login():
    """Serve admin login page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login - NekwasaR</title>
        <link rel="stylesheet" href="/static/css/main.css">
        <style>
            .login-container {
                max-width: 400px;
                margin: 100px auto;
                padding: 2rem;
                background: var(--base);
                border: 1px solid var(--stroke-elements);
                border-radius: var(--_radius-xl);
            }
            .login-form {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            .form-group {
                display: flex;
                flex-direction: column;
            }
            .form-group label {
                margin-bottom: 0.5rem;
                font-weight: 700;
            }
            .form-group input {
                padding: 0.75rem;
                border: 1px solid var(--stroke-elements);
                border-radius: var(--_radius-m);
                background: var(--base-tint);
                color: var(--t-bright);
            }
            .login-btn {
                padding: 0.75rem;
                background: linear-gradient(135deg, var(--accent), var(--secondary));
                color: var(--t-opp-bright);
                border: none;
                border-radius: var(--_radius-m);
                cursor: pointer;
                font-weight: 700;
                margin-top: 1rem;
            }
            .error-message {
                color: #ff6b6b;
                background: rgba(255, 107, 107, 0.1);
                padding: 0.5rem;
                border-radius: var(--_radius-s);
                margin-top: 1rem;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2 style="text-align: center; margin-bottom: 2rem;">Admin Login</h2>
            <form class="login-form" id="loginForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">Login</button>
            </form>
            <div id="errorMessage" class="error-message"></div>
        </div>

        <script>
            const loginForm = document.getElementById('loginForm');
            const errorMessage = document.getElementById('errorMessage');

            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            username: username,
                            password: password
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        localStorage.setItem('token', data.access_token);
                        window.location.href = '/admin/dashboard';
                    } else {
                        const error = await response.json();
                        showError(error.detail || 'Login failed');
                    }
                } catch (error) {
                    showError('Network error. Please try again.');
                }
            });

            function showError(message) {
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
                setTimeout(() => {
                    errorMessage.style.display = 'none';
                }, 5000);
            }
        </script>
    </body>
    </html>
    """

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve admin dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - NekwasaR</title>
        <link rel="stylesheet" href="/static/css/main.css">
        <style>
            .dashboard-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            .dashboard-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid var(--stroke-elements);
            }
            .messages-grid {
                display: grid;
                gap: 1rem;
            }
            .message-card {
                background: var(--base);
                border: 1px solid var(--stroke-elements);
                border-radius: var(--_radius-xl);
                padding: 1.5rem;
                transition: all 0.3s var(--_animbezier);
                cursor: pointer;
            }
            .message-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            }
            .message-card.unread {
                border-left: 4px solid var(--accent);
                background: linear-gradient(90deg, rgba(3, 0, 14, 0.05) 0%, var(--base) 20%);
            }
            .message-card.read {
                opacity: 0.7;
            }
            .message-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
            }
            .message-sender {
                font-weight: 700;
                color: var(--t-bright);
            }
            .message-date {
                font-size: 1.2rem;
                color: var(--t-muted);
            }
            .message-email {
                color: var(--t-medium);
                margin-bottom: 0.5rem;
            }
            .message-content {
                color: var(--t-medium);
                line-height: 1.5;
                margin-bottom: 1rem;
            }
            .message-actions {
                display: flex;
                gap: 1rem;
                justify-content: flex-end;
            }
            .btn-small {
                padding: 0.5rem 1rem;
                border: 1px solid var(--stroke-elements);
                background: var(--base);
                color: var(--t-bright);
                border-radius: var(--_radius-m);
                cursor: pointer;
                font-size: 1.2rem;
                transition: all 0.3s var(--_animbezier);
            }
            .btn-small:hover {
                background: var(--base-tint);
            }
            .btn-primary {
                background: linear-gradient(135deg, var(--accent), var(--secondary));
                color: var(--t-opp-bright);
                border: none;
            }
            .stats-bar {
                display: flex;
                gap: 2rem;
                margin-bottom: 2rem;
                padding: 1rem;
                background: var(--base-tint);
                border-radius: var(--_radius-xl);
            }
            .stat-item {
                text-align: center;
            }
            .stat-number {
                font-size: 2rem;
                font-weight: 700;
                color: var(--t-accent);
            }
            .stat-label {
                font-size: 1.2rem;
                color: var(--t-medium);
            }
            .loading {
                text-align: center;
                padding: 2rem;
                color: var(--t-medium);
            }
            .logout-btn {
                padding: 0.5rem 1rem;
                background: transparent;
                border: 1px solid var(--stroke-controls);
                color: var(--t-bright);
                border-radius: var(--_radius-m);
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="dashboard-header">
                <h1>Contact Messages</h1>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>

            <div class="stats-bar" id="statsBar">
                <div class="loading">Loading statistics...</div>
            </div>

            <div id="messagesContainer">
                <div class="loading">Loading messages...</div>
            </div>
        </div>

        <script>
            let allMessages = [];

            async function checkAuth() {
                const token = localStorage.getItem('token');
                if (!token) {
                    window.location.href = '/admin';
                    return;
                }

                try {
                    const response = await fetch('/api/auth/me', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!response.ok) {
                        localStorage.removeItem('token');
                        window.location.href = '/admin';
                    }
                } catch (error) {
                    localStorage.removeItem('token');
                    window.location.href = '/admin';
                }
            }

            async function loadMessages() {
                const token = localStorage.getItem('token');
                if (!token) return;

                try {
                    const response = await fetch('/api/contacts/', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        allMessages = await response.json();
                        renderMessages();
                        updateStats();
                    } else if (response.status === 401) {
                        localStorage.removeItem('token');
                        window.location.href = '/admin';
                    }
                } catch (error) {
                    console.error('Error loading messages:', error);
                }
            }

            function renderMessages() {
                const container = document.getElementById('messagesContainer');

                if (allMessages.length === 0) {
                    container.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--t-medium);">No messages yet.</p>';
                    return;
                }

                container.innerHTML = `
                    <div class="messages-grid">
                        ${allMessages.map(msg => `
                            <div class="message-card ${msg.is_read ? 'read' : 'unread'}" onclick="toggleMessage(this)">
                                <div class="message-header">
                                    <div class="message-sender">${escapeHtml(msg.name)}</div>
                                    <div class="message-date">${new Date(msg.created_at).toLocaleDateString()}</div>
                                </div>
                                <div class="message-email">${escapeHtml(msg.email)}</div>
                                <div class="message-content">${escapeHtml(msg.message)}</div>
                                <div class="message-actions">
                                    <button class="btn-small ${msg.is_read ? '' : 'btn-primary'}" onclick="markAsRead(${msg.id}, event)">
                                        ${msg.is_read ? 'Mark Unread' : 'Mark Read'}
                                    </button>
                                    <button class="btn-small" onclick="deleteMessage(${msg.id}, event)" style="color: #ff6b6b;">Delete</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            function updateStats() {
                const total = allMessages.length;
                const unread = allMessages.filter(msg => !msg.is_read).length;
                const read = total - unread;

                document.getElementById('statsBar').innerHTML = `
                    <div class="stat-item">
                        <div class="stat-number">${total}</div>
                        <div class="stat-label">Total</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number" style="color: var(--accent);">${unread}</div>
                        <div class="stat-label">Unread</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${read}</div>
                        <div class="stat-label">Read</div>
                    </div>
                `;
            }

            async function markAsRead(messageId, event) {
                event.stopPropagation();
                const token = localStorage.getItem('token');

                try {
                    const response = await fetch(`/api/contacts/${messageId}/read`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        // Update local data
                        const message = allMessages.find(msg => msg.id === messageId);
                        if (message) {
                            message.is_read = !message.is_read;
                            renderMessages();
                            updateStats();
                        }
                    }
                } catch (error) {
                    console.error('Error updating message:', error);
                }
            }

            async function deleteMessage(messageId, event) {
                event.stopPropagation();
                if (!confirm('Are you sure you want to delete this message?')) return;

                const token = localStorage.getItem('token');

                try {
                    const response = await fetch(`/api/contacts/${messageId}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        // Remove from local data
                        allMessages = allMessages.filter(msg => msg.id !== messageId);
                        renderMessages();
                        updateStats();
                    }
                } catch (error) {
                    console.error('Error deleting message:', error);
                }
            }

            function toggleMessage(card) {
                card.classList.toggle('expanded');
            }

            function logout() {
                localStorage.removeItem('token');
                window.location.href = '/admin';
            }

            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            // Initialize
            checkAuth();
            loadMessages();

            // Auto refresh every 30 seconds
            setInterval(loadMessages, 30000);
        </script>
    </body>
    </html>
    """

# Production Security Features (Commented for easy enabling)
"""
# HTTPS Enforcement (Uncomment in production)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

# Rate Limiting (Uncomment in production)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Enhanced CORS (Uncomment and configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"],  # Replace with your domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security Headers (Uncomment in production)
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "www.yourdomain.com"])

# Input Validation Enhancement (Uncomment in production)
from pydantic import validator, BaseModel

class SecureContactCreate(BaseModel):
    name: str
    email: str
    message: str

    @validator('name')
    def name_must_be_valid(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if not all(c.isalnum() or c.isspace() or c in ".-'" for c in v):
            raise ValueError('Name contains invalid characters')
        return v.strip()

    @validator('email')
    def email_must_be_valid(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @validator('message')
    def message_must_be_valid(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()

# Replace ContactCreate with SecureContactCreate in routes/contacts.py
"""

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)