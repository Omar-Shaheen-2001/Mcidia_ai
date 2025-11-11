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
-   **PDF Export**: WeasyPrint for HTML-to-PDF conversion (replaced ReportLab for better Arabic support).
-   **Excel Export**: OpenPyXL for Excel file generation.

### Frontend Libraries (CDN)
-   **Bootstrap 5**: UI framework.
-   **FontAwesome 6**: Icon library.
-   **Google Fonts**: Cairo and Poppins for web interface and PDF exports.
-   **Chart.js**: For interactive data visualization.

### PDF Export System (WeasyPrint)
-   **Implementation**: HTML/CSS templates converted to PDF using WeasyPrint (Nov 2025).
-   **Arabic Font**: Google Fonts Cairo loaded via CDN for reliable Arabic rendering.
-   **RTL Support**: Native CSS `direction: rtl` for proper right-to-left text layout.
-   **Professional Formatting**: Gradient headers, color-coded tables, responsive layouts, page breaks.
-   **Modules**:
    - `blueprints/pdf_export_weasy.py` - Strategic Identity module PDF export
    - `blueprints/pdf_export_strategic_planning.py` - Strategic Planning & KPIs module PDF export
-   **Exported Components**:
    - **Strategic Identity**: Vision, Mission, Core Values, SWOT Analysis, Strategic Objectives, **KPIs (NEW)**, Implementation Initiatives
    - **Strategic Planning**: Vision, Mission, Values, Strategic Goals, SWOT Analysis, PESTEL Analysis, KPIs, Strategic Initiatives
-   **Note**: Previous ReportLab implementation replaced due to Arabic text rendering issues with TTF fonts.

### KPI Generation System (Nov 2025)
-   **AI-Powered KPI Generator**: Automatically generates Key Performance Indicators (KPIs) for Strategic Identity projects based on strategic objectives
-   **Features**:
    - **Automatic Generation**: KPIs are generated automatically during strategic analysis workflow (integrated into `generate_analysis()`)
    - **Manual Regeneration**: Users can manually regenerate KPIs using the dashboard button
    - Generates 3-5 KPIs per strategic objective using AI
    - Each KPI includes: name, type (quantitative/qualitative), measurement unit, target value, current value, measurement frequency, responsible department
    - Linked to specific strategic objectives for traceability
    - Full CRUD operations (Create via AI, Read, Delete)
-   **Implementation**:
    - **Auto-Generation**: Integrated into `/generate-analysis` workflow (creates KPIs after objectives are saved)
    - Route: `/project/<id>/generate-kpis` (POST) - Manual KPI generation/regeneration
    - Route: `/project/<id>/kpis/<kpi_id>` (DELETE) - KPI deletion
    - Database: `identity_kpis` table with foreign keys to projects and objectives
    - UI: Interactive dashboard section with regeneration button and KPI display table
-   **Use Case Config**: `kpi_generation` in AIManager using HuggingFace Llama3 model (temperature: 0.6)
-   **Error Handling**: KPI generation errors are non-critical and logged; analysis continues even if KPI generation fails

### Dynamic Form Builder & Custom AI Prompts (Nov 2025)
-   **Dynamic Service Customization**: Admins can customize service offerings with dynamic form fields and personalized AI prompts
-   **Features**:
    - **Visual Form Builder**: Interactive UI to create custom input fields (text, textarea, number, email, date, select)
    - **Bilingual Field Support**: Each field has Arabic and English labels for full i18n
    - **Custom AI Prompts**: Admin-defined prompt templates with variable substitution `{field_name}`
    - **Dynamic Form Rendering**: User-facing forms automatically generated from JSON schema
    - **Schema-Driven Validation**: Server-side validation ensures data integrity
-   **Implementation**:
    - **Admin Interface**:
      - `templates/admin/services/create_offering.html` - Create offerings with form builder
      - `templates/admin/services/edit_offering.html` - Edit with field loading
      - Visual field editor with add/remove/reorder capabilities
      - Real-time JSON generation for storage
    - **User Interface**:
      - `templates/services/offering_detail.html` - Dynamic form generation
      - JavaScript parses `form_fields` JSON to render appropriate input types
      - Automatic field validation (required, type checking)
    - **API Integration** (`blueprints/services_bp.py`):
      - `/api/services/<service>/<offering>/generate` endpoint
      - **Uses HuggingFace AI via AIManager** (same as Strategic Planning modules)
      - Use case config: `custom_consultation` with llama3 model (temperature: 0.7, max_tokens: 3000)
      - Custom prompt template with `{field_name}` placeholder substitution
      - FormData serialization sends all dynamic + static fields
-   **Database Schema**:
    - `ServiceOffering.form_fields` (JSON): Array of field definitions
    - Format: `[{"name": "field_name", "type": "text|textarea|number|email|select|date", "label_ar": "...", "label_en": "...", "required": true|false, "options": [...]}]`
    - `ServiceOffering.ai_prompt_template` (Text): Custom prompt with variable placeholders
-   **Security**:
    - **Prompt Injection Protection**: Removes `{}` from user inputs before substitution
    - **Length Limiting**: Max 5000 characters per field to prevent abuse
    - **JSON Validation**: Admin input validated against schema structure
    - **Type Validation**: Server-side validation for numbers, emails, required fields
    - **Field Name Sanitization**: Only alphanumeric + underscore allowed
    - **Whitelisted Field Types**: Only predefined types accepted
-   **Example Use Case**:
    ```
    Admin creates "Market Analysis" offering with custom fields:
    - company_size (select: "Small", "Medium", "Large")
    - target_market (text, required)
    - annual_revenue (number)
    
    Custom prompt: "Provide market analysis for {project_name}. Company size: {company_size}. Target market: {target_market}. Annual revenue: {annual_revenue}."
    
    User fills form → API receives all fields → Prompt variables replaced with sanitized values → AI generates personalized consultation
    ```
-   **Benefits**:
    - **Flexible Offering Creation**: No code changes needed for new service types
    - **Personalized AI Responses**: Each offering can have specialized prompts
    - **Improved UX**: Tailored forms for specific consultation needs
    - **Scalability**: Easy to add new services without developer intervention

### Environment Configuration
-   Uses a `.env` file for sensitive credentials (API keys, database URLs, secret keys).
```