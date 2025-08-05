# Sister Share Shop - Community Donation Platform

## Overview

Sister Share Shop is a Flask-based web application that facilitates community-driven item sharing and donation. The platform connects people who want to donate items they no longer need with those who could benefit from them. Users can create donation listings with photos and descriptions, submit requests for needed items, and receive automated email notifications when matches occur. The system includes administrative oversight with approval workflows and comprehensive user management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 with dark theme support and Font Awesome icons
- **Responsive Design**: Mobile-first approach with Bootstrap's grid system
- **File Upload**: HTML5 file input with client-side validation for image uploads
- **Form Handling**: Flask-WTF for CSRF protection and form validation

### Backend Architecture
- **Web Framework**: Flask with modular structure separating routes, models, and forms
- **Authentication**: Flask-Login for session management with password hashing using Werkzeug
- **Database ORM**: SQLAlchemy with declarative base for model definitions
- **File Management**: Secure file uploads to static directory with filename sanitization
- **Email Service**: Flask-Mail for automated notifications and thank-you emails
- **Security**: CSRF protection, proxy fix for deployment, and input validation

### Data Models
- **User Model**: Handles authentication, profile data, and relationships to donations/requests
- **Category Model**: Organizes items into predefined categories for better navigation
- **Donation Model**: Tracks item donations with status workflow (pending → approved → donated)
- **Request Model**: Manages item requests with urgency levels and matching capabilities
- **Match Model**: Links donations to requests when items are matched
- **Notification Model**: Tracks communication history and automated email sending

### Database Design
- **Primary Database**: SQLite for development with PostgreSQL support for production
- **Connection Management**: Connection pooling with automatic reconnection
- **Migration Strategy**: SQLAlchemy migrations for schema evolution
- **Data Integrity**: Foreign key relationships and cascading deletes

### Authentication & Authorization
- **User Registration**: Email and username uniqueness validation
- **Session Management**: Secure session handling with remember-me functionality
- **Role-Based Access**: Admin users with elevated privileges for content moderation
- **Password Security**: Werkzeug password hashing with salt

### Email System
- **SMTP Configuration**: Gmail SMTP with TLS encryption
- **Automated Emails**: Thank-you messages to donors and match notifications
- **Template System**: HTML email templates with dynamic content
- **Error Handling**: Graceful fallback when email delivery fails

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework with routing and templating
- **Flask-SQLAlchemy**: Database ORM integration
- **Flask-Login**: User session management
- **Flask-WTF**: Form handling and CSRF protection
- **Flask-Mail**: Email sending capabilities

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI enhancement
- **Custom CSS**: Additional styling for brand consistency

### Database Support
- **SQLite**: Default development database
- **PostgreSQL**: Production database option via DATABASE_URL environment variable

### Email Service
- **SMTP Server**: Configurable email server (defaults to Gmail)
- **Email Templates**: HTML-based email formatting

### File Storage
- **Local Storage**: Static file serving for uploaded images
- **File Validation**: Image format restrictions (jpg, png, jpeg, gif)
- **Upload Limits**: 16MB maximum file size restriction

### Security & Deployment
- **Werkzeug**: Password hashing and development server
- **ProxyFix**: WSGI middleware for deployment behind reverse proxies
- **Environment Variables**: Configuration management for sensitive data