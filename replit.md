# Mcidia Platform

## Overview
Mcidia is an AI-powered B2B consulting platform offering over 12 specialized modules for organizational excellence, covering areas like strategic planning, HR, finance, and marketing. It supports bilingual interfaces (Arabic/English), features AI-driven consultation tools, manages subscriptions via Stripe, and implements robust role-based access control for various user types including admins, consultants, company users, and clients. The platform aims to provide comprehensive, AI-assisted guidance for businesses seeking to achieve strategic objectives and operational efficiency.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The frontend uses Flask/Jinja2 for server-side rendering, Bootstrap 5 for responsive UI, and a custom CSS design system for enterprise SaaS aesthetics. It supports bilingual (Arabic/English) RTL/LTR layouts with dynamic sidebar adjustments, using Cairo for Arabic typography and Poppins for English. The color palette is established with primary, secondary, and active UI colors, alongside semantic colors for states.

### Backend Architecture
The backend is built with Flask, utilizing a Blueprint-based modular architecture for organizing consulting domains like authentication, dashboard, profile, strategy, HR, and finance. Key components include:
- **Admin Panel**: A comprehensive panel with 13 sub-blueprints for managing users, billing, services, organizations, roles, AI, knowledge base, reports, and system settings. It supports CRUD operations, detailed organization management (including automatic owner account creation), and service/sub-service configuration with AI settings.
- **Organization Dashboards**: Separate dashboards for organization owners/admins (Org Admin Dashboard) and standard members (Org Member Dashboard) with role-specific functionalities and access control.
- **Authentication & Security**: Flask-JWT-Extended for JWT-based authentication, Flask-WTF for CSRF protection, and Flask-CORS.
- **URL Structure**: Consistent URL patterns for public services, admin panel, and organization-specific dashboards.

### Database & ORM
The platform uses Flask-SQLAlchemy with a PostgreSQL database (via Neon). Database connection pooling is configured for resilience. Core models include User, Role, SubscriptionPlan, Project, Transaction, AILog, and Document. New admin models include Organization, OrganizationSettings, OrganizationMembership, Notification, SupportTicket, SystemSettings, and AuditLog. A hierarchical role system is implemented with global system roles and organization-specific roles to ensure multi-tenancy and prevent privilege escalation. Custom migration scripts manage schema evolution.

### AI Integration
A pluggable multi-provider AI system utilizes an abstract `AIProvider` interface, allowing seamless switching between providers. The primary provider is HuggingFace (free tier) with models like Llama3, Mistral, and Mixtral, optimized for specific use cases (e.g., SWOT, PESTEL, KPI generation). OpenAI serves as an optional fallback. `AIManager` provides a simplified interface for use-case-optimized AI access, and `AILog` tracks AI usage.

### Authorization & Access Control
A hierarchical role system is enforced using custom Flask decorators (`@login_required`, `@role_required`, `@organization_role_required`). This system distinguishes between global system roles (e.g., `system_admin`) and organization-scoped roles (e.g., `owner`, `admin`, `member`) managed via the `OrganizationMembership` model, ensuring robust multi-tenant permission isolation.

## External Dependencies

### Third-Party Services
-   **HuggingFace Inference Providers**: Primary AI provider for consultation features (FREE with account!)
    - **Architecture** (Jan 2025 Update):
      - Uses new OpenAI-compatible API endpoint: `https://router.huggingface.co/v1/chat/completions`
      - Multi-provider routing system (SambaNova, Together AI, fal, Replicate, etc.)
      - Free tier includes monthly credits for all HuggingFace users
    - **Models** (2025 Chat-Compatible):
      - `deepseek-ai/DeepSeek-V3` (Best for complex reasoning)
      - `deepseek-ai/DeepSeek-R1` (Math, logic, coding with chain-of-thought)
      - `meta-llama/Llama-3.3-70B-Instruct` (Powerful instruction-following)
      - `meta-llama/Llama-3.1-8B-Instruct` (Fast, efficient, default)
      - `Qwen/Qwen2.5-72B-Instruct` (Multilingual, strong performance)
      - `Qwen/Qwen2.5-Coder-32B-Instruct` (Specialized for code generation)
    - **Authentication**: Requires `HUGGINGFACE_TOKEN` (free to obtain at https://huggingface.co/settings/tokens)
    - **Note**: Old endpoint (api-inference.huggingface.co) deprecated in 2025, returns 410 Gone
-   **OpenAI API**: Optional fallback AI provider (GPT-4, GPT-3.5-Turbo).
-   **Stripe**: Payment processing and subscription management.

### Database
-   **SQLAlchemy ORM**: For database abstraction.
-   **PostgreSQL**: Target database, currently using Replit's Neon-backed database.

### Python Packages
-   **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Flask-WTF.
-   **Security**: Werkzeug, python-dotenv.
-   **AI**: OpenAI Python client, LangChain, LangChain-Community, Requests.
-   **PDF Export**: ReportLab for PDF generation, arabic-reshaper and python-bidi for RTL text support.
-   **Excel Export**: OpenPyXL for Excel file generation.

### Frontend Libraries (CDN)
-   **Bootstrap 5**: UI framework.
-   **FontAwesome 6**: Icon library.
-   **Google Fonts**: Cairo and Poppins for web interface.
-   **Chart.js**: For interactive data visualization.

### PDF Export System
-   **Arabic Font**: Amiri (Regular & Bold) - Professional Arabic font optimized for PDF rendering.
-   **RTL Support**: Full right-to-left text support using arabic-reshaper and python-bidi.
-   **Professional Formatting**: Color-coded headers, alternating row colors, proper spacing and padding.
-   **Exported Components**: Vision, Mission, Core Values, SWOT Analysis, PESTEL Analysis, Strategic Objectives, KPIs, and Implementation Initiatives.

### Environment Configuration
-   Uses a `.env` file for sensitive credentials (API keys, database URLs, secret keys).
```