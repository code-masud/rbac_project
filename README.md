# RBAC Blog System - Role-Based Access Control Blog Platform

A production-ready blog system with comprehensive Role-Based Access Control (RBAC) built with Django, Django REST Framework, and Bootstrap 5.

## 📋 Table of Contents
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Roles & Permissions](#roles--permissions)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Core Features
- **Role-Based Access Control** with 4 distinct roles
- **JWT Authentication** with refresh tokens
- **Complete Blog System** (Posts & Comments)
- **Responsive Bootstrap 5 UI**
- **RESTful API** with full CRUD operations
- **Swagger/OpenAPI Documentation**
- **Pagination, Filtering & Search**
- **Soft Delete Functionality**
- **Django Admin Interface**
- **Production-Ready Configuration**

### User Features
- User registration and login
- Profile management
- Password change functionality
- View posts and comments (guests)
- Create, edit, delete own posts (regular users)
- Comment on posts (authenticated users)
- Delete own comments
- Post owners can delete comments on their posts

### Admin Features
- Super Admin: Full system access
- Moderator: Delete any content
- User management interface
- Role assignment
- Content moderation tools

## 🛠 Technology Stack

### Backend
- **Django 5.0.6** - Web framework
- **Django REST Framework 3.15.1** - API framework
- **Simple JWT** - JWT authentication
- **drf-spectacular** - OpenAPI documentation
- **django-filter** - Advanced filtering
- **Celery** - Task queue (optional)
- **Redis** - Caching & message broker

### Database
- **PostgreSQL** (Production)
- **SQLite** (Development)

### Frontend
- **Bootstrap 5.3** - UI framework
- **Bootstrap Icons** - Icon library
- **Custom CSS/JS** - Enhanced UX

### Tools & Libraries
- **Faker** - Sample data generation
- **Gunicorn** - WSGI server
- **python-dotenv** - Environment variables
- **django-cors-headers** - CORS support
- **django-debug-toolbar** - Debugging

## 👥 Roles & Permissions

### 1. Super Admin
- Full system access
- Delete any post/comment
- Manage users and roles
- Access Django admin
- View all system statistics

### 2. Moderator
- Delete any post
- Delete any comment
- Cannot manage users
- View all content

### 3. Regular User
- Create posts
- Update own posts only
- Delete own posts only
- Create comments
- Delete own comments
- Delete comments on own posts

### 4. Guest (Unauthenticated)
- View all posts and comments
- Cannot create/edit/delete anything
- Read-only access

### Permission Matrix

| Action | Super Admin | Moderator | Regular User | Guest |
|--------|-------------|-----------|--------------|-------|
| View posts | ✅ | ✅ | ✅ | ✅ |
| Create post | ✅ | ✅ | ✅ | ❌ |
| Edit own post | ✅ | ✅ | ✅ | ❌ |
| Edit others' post | ✅ | ❌ | ❌ | ❌ |
| Delete own post | ✅ | ✅ | ✅ | ❌ |
| Delete others' post | ✅ | ✅ | ❌ | ❌ |
| Create comment | ✅ | ✅ | ✅ | ❌ |
| Delete own comment | ✅ | ✅ | ✅ | ❌ |
| Delete others' comment | ✅ | ✅ | ❌* | ❌ |
| Manage users | ✅ | ❌ | ❌ | ❌ |

\* Post owners can delete comments on their posts

## 📥 Installation Guide

### Prerequisites
- Python 3.10 or higher
- PostgreSQL (optional, SQLite works for development)
- Git
- Virtual environment tool (venv/conda)

### Step 1: Clone the Repository

```bash
git clone https://github.com/code-masud/rbac_project
cd rbac_project

# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

python manage.py createsuperuser
# Email: admin@example.com
# Password: admin123
# Role will be automatically set to Super Admin

# Generate sample data with default settings
python manage.py generate_sample_data

# Generate specific amount of data
python manage.py generate_sample_data --users=50 --posts=200 --comments=500

# Clean existing data first
python manage.py generate_sample_data --clean

python manage.py collectstatic --noinput


# Run Django development server
python manage.py runserver

# Access the Application
Frontend: http://localhost:8000
Admin Interface: http://localhost:8000/admin/
API Documentation: http://localhost:8000/api/docs/
ReDoc Documentation: http://localhost:8000/api/redoc/