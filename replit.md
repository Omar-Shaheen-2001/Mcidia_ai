# Mcidia Platform

## Overview

Mcidia is a comprehensive AI-powered B2B consulting platform designed for organizational excellence. It provides 12+ specialized consulting modules covering strategic planning, human resources, governance, innovation, finance, marketing, and knowledge management. The platform features bilingual support (Arabic/English with RTL/LTR), AI-driven consultation tools, subscription management with Stripe integration, and role-based access control for admins, consultants, company users, and clients.

### Latest Updates (November 2025)
- **✅ Strategic Planning & KPIs Module (COMPLETE)**: Full AI-powered strategic planning module with SWOT/PESTEL analysis, vision/mission generation, KPI development, and comprehensive dashboard
  - URL: `/strategic-planning/`
  - Features: Organization data collection, AI-driven SWOT/PESTEL analysis, strategic framework generation (Vision/Mission/Goals), SMART KPI generation, interactive dashboard
  - AI Models: GPT-4 for strategic analysis
  - Database: StrategicPlan, StrategicKPI, StrategicInitiative tables

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Flask/Jinja2 server-side rendering
- **UI Framework**: Bootstrap 5 for responsive layouts
- **Design System**: Custom CSS design system (`design-system.css`) implementing enterprise SaaS aesthetics
- **Styling Approach**: CSS variables for theming, component-based styling with BEM-like naming
- **Bilingual Support**: RTL/LTR layout switching based on session language preference (Arabic/English) with proper sidebar collapse animation for both directions
- **Typography**: Cairo font for Arabic, Poppins for English
- **Color Palette**: Primary (#0A2756), Secondary (#2C8C56), Active UI (#2767B1), with semantic colors for success/warning/error states

**Rationale**: Server-side rendering provides SEO benefits and simplifies deployment while Bootstrap enables rapid development of responsive interfaces. The custom design system ensures brand consistency across 12+ modules.

### Backend Architecture
- **Framework**: Flask (Python) with Blueprint-based modular architecture
- **Module Organization**: 
  - Main blueprints for consulting domains (auth, dashboard, profile, strategy, hr, finance, etc.)
  - `profile`: User profile management with settings page (personal info, password change, preferences, plan usage, account deletion)
  - `org_dashboard`: **Organization Admin Dashboard** (Nov 2025)
    - Dedicated dashboard for organization owners/admins
    - Team management (member listing, role assignment)
    - Knowledge center (document management - placeholder)
    - Reports & analytics (performance metrics - placeholder)
    - Billing management (subscription & invoices - placeholder)
    - Organization settings (basic info, preferences)
    - Access controlled via `organization_role_required` decorator
  - `member_dashboard`: **Organization Member Dashboard** (Nov 2025 - NEW)
    - Simplified dashboard for organization employees (members)
    - 4 core modules: Dashboard, Modules, Reports, Knowledge Search
    - Dashboard: Personal statistics (projects, AI usage) and recent projects list
    - Modules: View and access only enabled modules per organization settings
    - Reports: View personal projects, results, and AI usage history
    - Knowledge Search: AI-powered search in organization documents
    - Access controlled via `organization_role_required('member')` decorator
    - Restricted permissions: No billing access, no team management, no org settings
  - Admin package with 13 sub-blueprints for comprehensive admin panel
- **Admin Structure**: Package-based architecture at `blueprints/admin/` with sub-blueprints:
  - `dashboard`: Main admin dashboard with charts (Chart.js) and statistics
  - `users`: Complete user management (CRUD, filtering, role assignment, password reset, phone number management)
  - `billing`: Transaction and payment management
  - `services_admin`: **Comprehensive Services & Sub-Services Management** (Nov 2025 - NEW)
    - Full CRUD operations for main consulting services (7 categories)
    - Complete sub-services management (25+ offerings) with AI configuration
    - Service features: bilingual titles, slugs, icons (FontAwesome), custom colors, display order
    - Sub-service AI settings: model selection (GPT-4/3.5/Turbo), prompt templates, credits cost, form fields (JSON)
    - Filtering and search capabilities for both services and offerings
    - Active/inactive status management (soft delete)
    - 6 HTML templates: services list, create/edit service, offerings list, create/edit offering
    - All routes protected with `@login_required` and `@role_required('system_admin')`
    - Database queries use `db.session.query(Model).filter_by().first_or_404()` pattern for SQLAlchemy compatibility
  - `organizations`: **Comprehensive multi-tenant organization management** (Nov 2025 Enhanced)
    - List view with search, filters (status, plan, sector), and CSV export
    - Detailed organization profile with tabs: Overview, Users, Billing, Analytics, Settings
    - CRUD operations for organizations
    - **Automatic Admin Account Creation** (Nov 2025 - NEW):
      - On organization creation, automatically creates owner account with secure generated password
      - Validates admin email uniqueness and prevents duplicate accounts
      - Displays generated password one-time only after creation
      - Creates OrganizationMembership with 'owner' role for full org control
    - User management per organization
    - Organization-specific settings (language, timezone, AI preferences, module access)
    - Performance analytics with Chart.js visualization (AI usage, project stats)
    - AI usage tracking and reset functionality
    - Suspend/activate organizations
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
  - Organization dashboard: `/org/*` (organization role-restricted for owners/admins)
  - Member dashboard: `/member/*` (organization role-restricted for members)

**Rationale**: Flask's lightweight nature and blueprint system allows clean separation of 12+ consulting modules. Package-based admin structure enables scalability and maintainability. JWT provides stateless authentication suitable for potential API expansion.

### Database & ORM
- **ORM**: Flask-SQLAlchemy (SQLAlchemy core)
- **Database**: PostgreSQL (via Replit's built-in Neon-backed database)
- **Connection Pooling** (Nov 2025 - FIXED):
  - Configured with `pool_pre_ping=True` to automatically reconnect on SSL disconnects
  - `pool_recycle=300` to refresh connections every 5 minutes
  - `pool_size=10` and `max_overflow=20` for optimal performance
  - Resolves "SSL connection has been closed unexpectedly" errors
- **Models**: 
  - **Core Models**: User, Role, SubscriptionPlan, Project, Transaction, AILog, Document
  - **Admin Models** (added Nov 2025):
    - `Organization`: Multi-tenant organization management with comprehensive fields (sector, city, website, logo_url, plan_type, subscription_status, ai_usage_limit/current)
    - `OrganizationSettings`: Granular organization-specific settings (language, timezone, notifications, AI preferences, enabled modules)
    - `OrganizationMembership`: **Hierarchical role system** (Nov 2025 - CRITICAL SECURITY FIX)
      - Links users to organizations with organization-specific roles (owner, admin, member)
      - Prevents privilege escalation: organization admins only have org-scoped access
      - Unique constraint: one membership per user per organization
    - `Notification`: System-wide notification tracking
    - `SupportTicket`: Customer support ticket system
    - `SystemSettings`: Platform-wide configuration key-value store
    - `AuditLog`: Comprehensive audit trail for admin actions
- **Schema Design**: 
  - **Hierarchical Role System** (Nov 2025):
    - Global roles: system_admin (platform admin), external_user (default), consultant, company_user, client
    - Organization roles (in OrganizationMembership): owner (full org control), admin (user/settings management), member (standard access)
  - Subscription plans (free, monthly, yearly, pay_per_use) with AI credits tracking
  - User authentication with password hashing via Werkzeug
  - User enhancements: `organization_id` (multi-tenancy), `is_active` (soft delete), `last_login` (tracking), `phone` (contact information)
- **Migration**: Custom migration scripts
  - `migrate_admin_models.py`: Initial admin models
  - `migrate_organizations.py`: Organizations and settings tables
  - `migrate_roles_and_memberships.py`: **Hierarchical roles system** (renames 'admin' to 'system_admin', creates OrganizationMembership table, migrates existing users)

**Rationale**: SQLAlchemy provides database abstraction allowing future migration to different databases. The role-subscription model supports flexible business models and usage-based billing. Organization model enables multi-tenant B2B scenarios. Audit logging ensures compliance and security.

### AI Integration
- **Provider**: OpenAI API (GPT-5 model)
- **Centralized Client**: `utils/ai_client.py` provides `llm_chat()` function for consistent AI interactions
- **Usage Tracking**: AILog model tracks prompts, responses, and token consumption per user/module
- **Features**: System prompt configuration, JSON response formatting, token estimation

**Rationale**: Centralized AI client ensures consistent error handling and usage tracking across all 12+ modules. Token tracking enables pay-per-use billing model.

### Authorization & Access Control
- **Hierarchical Role System** (Nov 2025 Enhanced):
  - **Global System Roles**: Platform-wide permissions (system_admin, external_user, consultant, company_user, client)
  - **Organization Roles**: Organization-scoped permissions via OrganizationMembership model (owner, admin, member)
- **Custom Decorators** in `utils/decorators.py`:
  - `@login_required`: JWT authentication verification
  - `@role_required('system_admin')`: Global system role verification (for admin panel access)
  - `@organization_role_required('owner', 'admin')`: Organization-scoped role verification (NEW)
- **JWT Verification**: Request-level JWT validation with identity extraction
- **Permission Model**: 
  - Global roles stored in Role model
  - Organization-specific roles stored in OrganizationMembership model
  - Prevents privilege escalation: organization admins cannot access system-wide admin panel

**Rationale**: Hierarchical permission system prevents critical security vulnerability where organization admins were gaining system-wide access. OrganizationMembership model enables true multi-tenant role isolation.

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