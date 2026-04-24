# ChatFlick 🐦

> A modern social microblogging platform built with Flask — share thoughts, follow people, and chat with an AI assistant.

## 🔗 Live Demo
Access the application here:  
https://chatflick.pythonanywhere.com

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red?style=flat-square)
![Firebase](https://img.shields.io/badge/Firebase-Push_Notifications-FFCA28?style=flat-square&logo=firebase&logoColor=black)
![Cloudinary](https://img.shields.io/badge/Cloudinary-Media_Storage-3448C5?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-AI_Powered-FF6B35?style=flat-square)

---

## ✨ Features

### 🔐 Authentication
- Email & password signup with CAPTCHA (Cloudflare Turnstile)
- Google OAuth login
- Email verification flow with time-limited tokens
- Secure password reset via email link

### 📝 Posts & Feed
- Create, edit, and delete posts (within a 3-minute window)
- Automatic hashtag extraction and `@mention` parsing
- Home feed with **For You** (random) and **Following** tabs
- Like, repost, share, and comment on posts
- Milestone notifications at 100 / 1K / 10K likes and reposts

### 👥 Social Graph
- Follow and unfollow users
- Follower and following counts on profiles
- Explore page with account search and random suggestions

### 🔔 Notifications
- In-app notification inbox with unread badge
- Firebase Cloud Messaging (FCM) push notifications
- Deduplication for repeat events (likes, follows)
- Mention notifications on posts and comments

### 🤖 Manzoid-AI
- Groq-powered AI assistant (LLaMA 3.1 8B)
- Authenticated chat with short-term memory (last 2 exchanges)
- Public stateless chat endpoint
- Great for generating tweet ideas, rewrites, hashtags, and summaries

### ⚙️ Settings
- Profile info, bio, website, and contact management
- Email, password, and birthdate changes
- Privacy controls (private account, show/hide bio, birthdate, follower counts)
- Notification preferences (push, email, mentions, reposts, likes)
- Light / Dark theme toggle
- Account data export as `.zip`
- Account deactivation and deletion

### 🛡️ Admin Dashboard
- Full admin panel at `/admin`
- Manage support requests and bug reports
- Verify users, approve/reject Pro status, send warnings, block/unblock accounts
- Real-time metrics: total users, pending requests, verified accounts

---

## 🗂️ Project Structure

```
ChatFlick/
├── app/
│   ├── models/          # SQLAlchemy models (User, Post, Comment, Follow, Notification…)
│   ├── routes/          # Flask Blueprints (auth, post, profile, settings, admin…)
│   ├── services/        # Business logic layer
│   ├── utils/           # Helpers (mentions parser, username builder)
│   ├── firebase/        # Firebase Admin SDK init
│   ├── cloudinary/      # Cloudinary config
│   ├── oauth/           # Google OAuth setup
│   └── decorators.py    # Auth guards (verified_user, pro_user, only_admin)
├── templates/           # Jinja2 HTML templates
├── static/
│   ├── css/             # Stylesheets (styles.css, styles01.css, setting.css, AI.css…)
│   └── js/              # Client-side scripts (home.js, setting.js, admin.js…)
├── main.py              # App entry point
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A PostgreSQL or SQLite database
- Cloudinary account
- Firebase project (for push notifications)
- Groq API key
- Google OAuth credentials (optional)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-username/chatflick.git
cd chatflick

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file and fill in your values
cp .env.example .env
```

### Environment Variables

Create a `.env` file in the project root:

```env
# App
SECRET_KEY=your-secret-key

# Database
SQLALCHEMY_DATABASE_URI=sqlite:///chatflick.db

# Email (Gmail SMTP)
EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Google OAuth
CLIENT_ID=your-google-client-id
CLIENT_SECRET=your-google-client-secret

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Firebase
FIREBASE_SERVICE_ACCOUNT=path/to/service-account.json
FCM_VAPID_KEY=your-vapid-key
FIREBASE_API_KEY=your-firebase-api-key

# Groq AI
GROQ_API_KEY=your-groq-api-key

# Cloudflare Turnstile CAPTCHA
CLOUDFARE_SECRET_KEY=your-turnstile-secret
```

### Run the App

```bash
python main.py
```

The app will be available at `http://localhost:5000`.

---

## 🧩 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask, SQLAlchemy, Flask-Login, Authlib |
| Database | PostgreSQL / SQLite |
| Frontend | Jinja2, Bootstrap 5, jQuery, Bootstrap Icons |
| Media Storage | Cloudinary |
| Push Notifications | Firebase Cloud Messaging |
| AI Assistant | Groq (LLaMA 3.1 8B Instant) |
| CAPTCHA | Cloudflare Turnstile |
| Image Cropping | Cropper.js |

---

## 📸 Key Pages

| Route | Description |
|---|---|
| `/` | Landing page |
| `/home` | Main feed (For You / Following) |
| `/profile/<id>` | User profile |
| `/notifications` | Notification inbox |
| `/Manzoid-AI` | AI chat assistant |
| `/setting` | Account settings |
| `/admin` | Admin dashboard (admin only) |

---

## 🔒 User Status Levels

| Status | Description |
|---|---|
| `UNVERIFIED` | Newly registered, limited access |
| `VERIFIED` | Email confirmed, full access |
| `PRO` | Premium user with Pro badge |
| `DEACTIVED` | Temporarily deactivated |
| `BLOCKED` | Restricted by admin |

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">Built with ❤️ by <strong>coreXmanzoid</strong></p>
