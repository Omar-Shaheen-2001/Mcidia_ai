# Mcidia Platform

## Overview

Mcidia is a comprehensive AI-powered B2B consulting platform designed for organizational excellence. It provides 12+ specialized consulting modules covering strategic planning, human resources, governance, innovation, finance, marketing, and knowledge management. The platform features bilingual support (Arabic/English with RTL/LTR), AI-driven consultation tools, subscription management with Stripe integration, and role-based access control for admins, consultants, company users, and clients.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Flask/Jinja2 server-side rendering
- **UI Framework**: Bootstrap 5 for responsive layouts
- **Design System**: Custom CSS design system (`design-system.css`) implementing enterprise SaaS aesthetics
- **Styling Approach**: CSS variables for theming, component-based styling with BEM-like naming
- **Bilingual Support**: RTL/LTR layout switching based on session language preference (Arabic/English)
- **Typography**: Cairo font for Arabic, Poppins for English
- **Color Palette**: Primary (#0A2756), Secondary (#2C8C56), Active UI (#2767B1), with semantic colors for success/warning/error states

**Rationale**: Server-side rendering provides SEO benefits and simplifies deployment while Bootstrap enables rapid development of responsive interfaces. The custom design system ensures brand consistency across 12+ modules.

### Backend Architecture
- **Framework**: Flask (Python) with Blueprint-based modular architecture
- **Module Organization**: 
  - Main blueprints for consulting domains (auth, dashboard, strategy, hr, finance, etc.)
  - Admin package with 13 sub-blueprints for comprehensive admin panel
- **Admin Structure**: Package-based architecture at `blueprints/admin/` with sub-blueprints:
  - `dashboard`: Main admin dashboard with charts (Chart.js) and statistics
  - `users`: Complete user management (CRUD, filtering, role assignment, password reset)
  - `billing`: Transaction and payment management
  - `services_admin`: Service configuration and management
  - `organizations`: Multi-tenant organization management
  - `roles`: Role and permission management
  - `ai_management`: AI usage monitoring and credit management
  - `knowledge_admin`: Knowledge base content management
  - `reports`: Business intelligence and reporting
  - `notifications_admin`: System notification management
  - `settings`: Platform configuration and settings
  - `logs`: Audit trail and system logs
  - `support`: Support ticket system
- **Authentication**: Flask-JWT-Extended for JWT-based authentication with cookie storage
- **Security**: Flask-WTF CSRF protection, Flask-CORS for cross-origin requests
- **Session Management**: Server-side sessions for language preferences and user state
- **URL Structure**: 
  - Public services: `/services/*`
  - Admin panel: `/admin/*` (role-restricted, redirects `/admin/` to `/admin/dashboard/`)

**Rationale**: Flask's lightweight nature and blueprint system allows clean separation of 12+ consulting modules. Package-based admin structure enables scalability and maintainability. JWT provides stateless authentication suitable for potential API expansion.

### Database & ORM
- **ORM**: Flask-SQLAlchemy (SQLAlchemy core)
- **Database**: PostgreSQL (via Replit's built-in Neon-backed database)
- **Models**: 
  - **Core Models**: User, Role, SubscriptionPlan, Project, Transaction, AILog, Document
  - **Admin Models** (added Nov 2025):
    - `Organization`: Multi-tenant organization management with settings
    - `Notification`: System-wide notification tracking
    - `SupportTicket`: Customer support ticket system
    - `SystemSettings`: Platform-wide configuration key-value store
    - `AuditLog`: Comprehensive audit trail for admin actions
- **Schema Design**: 
  - Role-based access with 4 default roles (admin, consultant, company_user, client)
  - Subscription plans (free, monthly, yearly, pay_per_use) with AI credits tracking
  - User authentication with password hashing via Werkzeug
  - User enhancements: `organization_id` (multi-tenancy), `is_active` (soft delete), `last_login` (tracking)
- **Migration**: Custom migration scripts (e.g., `migrate_admin_models.py`) for schema updates

**Rationale**: SQLAlchemy provides database abstraction allowing future migration to different databases. The role-subscription model supports flexible business models and usage-based billing. Organization model enables multi-tenant B2B scenarios. Audit logging ensures compliance and security.

### AI Integration
- **Provider**: OpenAI API (GPT-5 model)
- **Centralized Client**: `utils/ai_client.py` provides `llm_chat()` function for consistent AI interactions
- **Usage Tracking**: AILog model tracks prompts, responses, and token consumption per user/module
- **Features**: System prompt configuration, JSON response formatting, token estimation

**Rationale**: Centralized AI client ensures consistent error handling and usage tracking across all 12+ modules. Token tracking enables pay-per-use billing model.

### Authorization & Access Control
- **Custom Decorators**: `@login_required` and `@role_required` decorators in `utils/decorators.py`
- **JWT Verification**: Request-level JWT validation with identity extraction
- **Permission Model**: Role-based permissions stored as JSON in Role model

**Rationale**: Decorator pattern provides reusable authorization logic. Role-based system supports multi-tenant consulting scenarios with different access levels.

## External Dependencies

### Third-Party Services
- **OpenAI API**: AI-powered consultation features (GPT-5)
  - API key via `OPENAI_API_KEY` environment variable
  - Used across consultation, strategy, HR, and other modules
  
- **Stripe**: Payment processing and subscription management
  - API key via `STRIPE_SECRET_KEY` environment variable
  - Customer creation, subscription handling, transaction tracking

### Database
- **Current**: SQLAlchemy ORM (database-agnostic)
- **Expected**: PostgreSQL (not yet configured but likely target for production)
- **Seeding**: Default roles and subscription plans seeded on app initialization

### Python Packages
- **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Flask-WTF
- **Security**: Werkzeug (password hashing), python-dotenv (environment management)
- **AI**: OpenAI Python client library

### Frontend Libraries (CDN)
- **Bootstrap 5**: UI framework and components
- **FontAwesome 6**: Icon library
- **Google Fonts**: Cairo (Arabic), Poppins (English)
- **Chart.js**: Interactive charts for admin dashboard analytics (user growth, revenue, AI usage)

### Environment Configuration
- `.env` file for sensitive credentials (API keys, database URLs, secret keys)
- Session secret key for Flask sessions
- JWT secret key for token signing