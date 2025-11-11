# Mcidia Platform

## Overview
Mcidia is an AI-powered B2B consulting platform designed to provide comprehensive, AI-assisted guidance for businesses. It offers over 12 specialized modules for organizational excellence, covering strategic planning, HR, finance, and marketing. Key capabilities include AI-driven consultation, bilingual (Arabic/English) interfaces, subscription management via Stripe, and robust role-based access control for various user types. The platform aims to help businesses achieve strategic objectives and operational efficiency.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The frontend uses Flask/Jinja2 for server-side rendering, Bootstrap 5 for responsive UI, and a custom CSS design system. It supports bilingual (Arabic/English) RTL/LTR layouts with dynamic sidebar adjustments, using Cairo for Arabic typography and Poppins for English.

### Backend Architecture
Built with Flask, the backend employs a Blueprint-based modular architecture. It includes a comprehensive Admin Panel for managing users, billing, services, organizations, roles, AI settings, and system configurations. Organization Dashboards provide role-specific functionalities for owners/admins and members. Authentication uses Flask-JWT-Extended, Flask-WTF for CSRF, and Flask-CORS.

### Database & ORM
The platform utilizes Flask-SQLAlchemy with a PostgreSQL database (Neon), configured for connection pooling. Core models manage users, roles, subscriptions, projects, transactions, AI logs, and documents. A hierarchical role system with global and organization-specific roles ensures multi-tenancy and robust access control.

### AI Integration
A pluggable multi-provider AI system uses an abstract `AIProvider` interface. The primary provider is HuggingFace (Llama3, Mistral, Mixtral) with OpenAI as an optional fallback. `AIManager` provides a simplified interface for use-case-optimized AI access, and `AILog` tracks AI usage. The system supports AI-powered KPI generation and dynamic consultation based on custom prompts.

### Authorization & Access Control
A hierarchical role system, enforced by custom Flask decorators (`@login_required`, `@role_required`, `@organization_role_required`), differentiates between global system roles and organization-scoped roles, managed via the `OrganizationMembership` model, ensuring multi-tenant permission isolation.

### Dynamic Form Builder & Custom AI Prompts
Admins can customize service offerings with dynamic form fields and personalized AI prompts. This includes a visual form builder with bilingual field support, custom prompt templates with variable substitution, and dynamic form rendering for user interfaces. This system enables flexible offering creation and personalized AI responses without code changes.

### Saved Consultations & Project View System
All generated consultations are automatically saved as projects. These are accessible from the user dashboard, displaying service metadata and offering one-click access to detailed project views. The project view page displays input data, AI output, and supports printing.

### PDF Export System (WeasyPrint)
HTML/CSS templates are converted to PDF using WeasyPrint for professional reporting. It includes robust Arabic font rendering (Cairo), RTL support, and professional formatting for modules like Strategic Identity and Strategic Planning.

### KPI Generation System
AI-powered KPI generation automatically creates 3-5 KPIs per strategic objective during strategic analysis workflows, with options for manual regeneration. Each KPI includes details like name, type, measurement unit, target, and frequency.

## External Dependencies

### Third-Party Services
-   **HuggingFace Inference Providers**: Primary AI provider for consultation features (e.g., Llama3, DeepSeek-V3).
-   **OpenAI API**: Optional fallback AI provider (GPT-4, GPT-3.5-Turbo).
-   **Stripe**: Payment processing and subscription management.

### Database
-   **SQLAlchemy ORM**: For database abstraction.
-   **PostgreSQL**: Target database, using Replit's Neon-backed database.

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