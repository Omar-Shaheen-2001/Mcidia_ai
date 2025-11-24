# Mcidia Platform

## Overview
Mcidia is an AI-powered B2B consulting platform offering over 12 specialized modules for organizational excellence, including strategic planning, HR, finance, and marketing. It provides AI-driven consultation, bilingual (Arabic/English) interfaces, subscription management via Stripe, and robust role-based access control. The platform aims to enhance strategic objectives and operational efficiency for businesses.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend
The frontend uses Flask/Jinja2 for server-side rendering, Bootstrap 5 for responsive UI, and a custom CSS design system. It supports bilingual (Arabic/English) RTL/LTR layouts with dynamic sidebar adjustments and specific font choices for each language.

### Backend
Built with Flask, the backend features a Blueprint-based modular architecture. It includes an Admin Panel for managing users, billing, services, organizations, roles, and AI settings. Organization Dashboards provide role-specific functionalities. Authentication is handled by Flask-JWT-Extended, Flask-WTF for CSRF, and Flask-CORS.

### Database & ORM
Flask-SQLAlchemy with a PostgreSQL database (Neon) is used. Core models manage users, roles, subscriptions, projects, and AI logs. A hierarchical role system supports multi-tenancy and robust access control.

### HR Employee Numbering System
The platform implements atomic employee number generation with full concurrency safety:
- **Multi-Tenant Constraint**: `employee_number` is unique per organization (composite constraint on `organization_id, employee_number`), allowing different organizations to use the same employee numbers independently.
- **Sequence Table**: Dedicated `employee_number_sequences` table stores the last used number for each organization, enabling atomic number allocation via `UPDATE ... RETURNING`.
- **Concurrency Safety**: Database-level row locking ensures no race conditions even under unlimited concurrent employee creation requests.
- **Pattern**: `INSERT ... ON CONFLICT DO NOTHING` + `UPDATE ... RETURNING last_number` provides atomic, wait-free number generation.
- **Migration**: See `migrations/001_fix_employee_number_constraints.sql` for schema changes.

### AI Integration
A pluggable multi-provider AI system uses an abstract `AIProvider` interface, primarily HuggingFace (Llama3, Mistral, Mixtral) with OpenAI as an optional fallback. `AIManager` simplifies AI access for various use cases, and `AILog` tracks usage. The system supports AI-powered KPI generation and dynamic consultation.

### Authorization & Access Control
A hierarchical role system enforced by custom Flask decorators (`@login_required`, `@role_required`, `@organization_role_required`, `@require_org_context`) manages global and organization-scoped roles, ensuring multi-tenant permission isolation.

### Centralized Tenancy & Auto-Provisioning
The platform features a centralized tenancy system that automatically provisions organizations for users on their first module access:
- **Tenancy Utility** (`utils/tenant.py`): Provides `get_or_create_user_org(session, user)` function that idempotently creates organizations with race-condition guards and transaction safety.
- **Auto-Provisioning Decorator** (`@require_org_context`): Automatically creates organizations and memberships for users without existing organizations, enabling immediate access to organization-scoped modules like HR.
- **User Flow**: Registration creates User only (no org); organization provisioning happens automatically on first module access with membership_role='owner'.
- **Benefits**: DRY code, consistent org creation, no manual setup required for new users.

### Dynamic Form Builder & Custom AI Prompts
Admins can customize service offerings with dynamic form fields and personalized AI prompts. This includes a visual form builder with bilingual field support, custom prompt templates with variable substitution, and dynamic form rendering for flexible offering creation and personalized AI responses.

### Saved Consultations & Project View
All generated consultations are saved as projects, accessible from the user dashboard. Project views display input data, AI output, and support printing.

### Professional PDF & Excel Export System
The platform includes a comprehensive export system for generating professionally formatted PDF and Excel files that mirror the web interface's visualization.
-   **PDF Export**: Uses WeasyPrint to convert HTML to PDF, supporting visual components, dynamic service colors, and proper typography for both Arabic and English.
-   **Excel Export**: Uses OpenPyXL for structured Excel generation, featuring service-themed headers, structured sections, and RTL support.
-   Both exports use a server-side Markdown formatter (`utils/markdown_formatter.py`) to ensure consistency with the frontend.

### KPI Generation System
AI-powered KPI generation automatically creates 3-5 KPIs per strategic objective during strategic analysis workflows, with options for manual regeneration, including details like name, type, measurement unit, target, and frequency.

### Enhanced AI Consultation Display
AI consultation outputs are transformed into professionally formatted displays with cards, grids, tables, and stat boxes using Marked.js for Markdown to HTML conversion and DOMPurify for XSS protection. This includes dynamic content transformation via JavaScript for visual components and enhanced styling with CSS. AI prompts are designed to encourage structured Markdown output for optimal visualization.

### Comprehensive AI Logs Admin Panel (/admin/ai/)
A fully-featured administrative dashboard for tracking all AI interactions with:
- **Core Metrics**: Total requests, success rate, failed requests, total cost
- **Request Details**: User, organization, service type, AI provider (OpenAI/HuggingFace), model name, execution time
- **Content Tracking**: Full prompt and response logging with code highlighting
- **Status Tracking**: Success/failed/timeout with error messages for debugging
- **Cost Calculation**: Estimated costs per request based on tokens and provider pricing
- **Advanced Filtering**: Filter by user, organization, service type, provider, status, date range, and full-text search
- **Pagination**: 50 records per page with navigation
- **Statistics API**: `/api/stats` endpoint for daily stats, provider breakdown, service breakdown
- **Detailed View**: Individual log details page with copy-to-clipboard functionality
- **Bilingual**: Full Arabic/English support with RTL/LTR layouts

## External Dependencies

### Third-Party Services
-   **HuggingFace Inference Providers**: Primary AI provider (e.g., Llama3, DeepSeek-V3).
-   **OpenAI API**: Optional fallback AI provider (GPT-4, GPT-3.5-Turbo).
-   **Stripe**: Payment processing and subscription management.

### Database
-   **SQLAlchemy ORM**: Database abstraction.
-   **PostgreSQL**: Target database, using Neon.

### Python Packages
-   **Flask Ecosystem**: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS, Flask-WTF.
-   **Security**: Werkzeug, python-dotenv.
-   **AI**: OpenAI Python client, LangChain, LangChain-Community, Requests.
-   **PDF Export**: WeasyPrint.
-   **Excel Export**: OpenPyXL.

### Frontend Libraries (CDN)
-   **Bootstrap 5**: UI framework.
-   **FontAwesome 6**: Icon library.
-   **Google Fonts**: Cairo and Poppins.
-   **Chart.js**: For interactive data visualization.
-   **Marked.js**: Markdown to HTML conversion.
-   **DOMPurify**: HTML sanitization.