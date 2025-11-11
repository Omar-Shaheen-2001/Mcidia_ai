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

### Professional PDF & Excel Export System
A comprehensive export system that generates beautifully formatted PDF and Excel files matching the rich web interface visualization with cards, grids, tables, and stat boxes.

**Architecture:**
- **Python Markdown Formatter** (`utils/markdown_formatter.py`): Server-side formatter that replicates frontend JavaScript logic
  - `format_consultation_output()`: Converts Markdown to formatted HTML with visual components
  - `clean_markdown_for_excel()`: Cleans Markdown syntax for Excel display
  - `extract_sections_from_markdown()`: Extracts structured sections from AI output
  - Mirror logic ensures PDF/Excel match web interface exactly

**PDF Export (WeasyPrint):**
- Route: `/services/project/<project_id>/export-pdf`
- Technology: WeasyPrint library converts HTML to PDF
- Template: `templates/exports/project_export.html` (dedicated export template with inline CSS)
- Features:
  - **Visual Components**: Cards, info grids, stat boxes, formatted tables
  - **Dynamic Service Colors**: Headers and accents use service-specific color schemes
  - **Typography**: Cairo font for Arabic, Poppins for English with proper RTL/LTR
  - **Professional Layout**: Title banner, structured sections, print-optimized A4 format
  - **Markdown Processing**: Full support for headings, lists, tables, bold text
  - **Gradient Styling**: Service-themed gradients for headers, cards, and tables
- Implementation:
  - Uses `format_consultation_output()` to transform Markdown into formatted HTML
  - Renders via dedicated template with inline CSS for WeasyPrint compatibility
  - Google Fonts loaded via HTTPS for consistent typography
- Security: JWT authentication with ownership verification

**Excel Export (OpenPyXL):**
- Route: `/services/project/<project_id>/export-excel`
- Technology: OpenPyXL library for Excel file generation
- Features:
  - **Service-Themed Headers**: Dynamic colors matching service branding
  - **Structured Sections**: Project info, input data, AI results with clear visual hierarchy
  - **Professional Styling**: Gradient fills, bold fonts, alternating row colors
  - **RTL Support**: Proper right-to-left text alignment for Arabic content
  - **Smart Row Heights**: Auto-adjusted based on content length
  - **Section Extraction**: AI output parsed into titled sections for clarity
  - **Markdown Cleanup**: Formatted text without Markdown syntax clutter
- Implementation:
  - Uses `extract_sections_from_markdown()` to structure AI output
  - Uses `clean_markdown_for_excel()` to remove Markdown formatting
  - 5-column layout (A-E) with merged cells for better readability
  - Title banner with service color, metadata rows, structured content sections
- Security: JWT authentication with ownership verification

**UI Integration:**
- Static export buttons in project view page (`project_view.html`)
- Dynamic export buttons in live consultation results (`offering_detail.html`)
- JavaScript function `addExportButtons(projectId)` adds buttons after AI generation
- Color-coded buttons: Red for PDF, Green for Excel

**Authentication & Security:**
- Both routes use `@login_required` decorator
- JWT identity verification via `get_jwt_identity()`
- Returns 401 if authentication fails
- Returns 403 if user doesn't own the project
- Returns 404 if project not found

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
-   **Marked.js**: Markdown to HTML conversion for AI consultation output.
-   **DOMPurify**: HTML sanitization library for XSS protection.

## Recent Enhancements (November 2025)

### Enhanced AI Consultation Display
A comprehensive visualization system transforms AI consultation outputs from plain text into professionally formatted displays with cards, grids, tables, and stat boxes.

**Implementation Details:**

1. **Markdown Processing** (`templates/services/project_view.html`):
   - **Marked.js (v4.x)**: Converts AI output from Markdown to HTML
   - **DOMPurify (v3.0.6)**: Sanitizes generated HTML to prevent XSS attacks
   - Whitelist-based security: Only allows safe HTML tags (headings, lists, tables, emphasis)
   - No event handlers or data attributes permitted

2. **Dynamic Content Transformation** (JavaScript):
   - **Card Lists**: Converts bullet lists (3+ items) into interactive card grids
   - **Info Grids**: Transforms key-value pairs into responsive grid layouts
   - **Stat Boxes**: Identifies numeric patterns (e.g., "75% - Success Rate") and renders them as highlighted statistics
   - **Table Enhancement**: Wraps tables in responsive containers for mobile compatibility

3. **Visual Styling** (CSS):
   - **Cards**: Gradient backgrounds, colored borders, hover elevation effects
   - **Tables**: Gradient headers (primary color), alternating row colors, hover highlighting
   - **Stat Boxes**: Purple gradient backgrounds, large numbers, descriptive labels
   - **Grid Items**: White backgrounds, subtle shadows, hover animations
   - **Typography**: Enhanced line-height (2.0), larger font size (1.05rem), hierarchical headings

4. **AI Prompt Enhancement** (`blueprints/services_bp.py`):
   - Markdown instructions appended to all system prompts (custom + default)
   - Requests structured output with:
     - Headings (#, ##, ###) for content organization
     - Unordered lists (3+ items) for key points
     - Numbered lists for steps/phases
     - Tables for structured data
     - **Bold text** for emphasis
     - Formatted statistics (e.g., "number - description")

5. **Security Measures**:
   - **XSS Prevention**: DOMPurify sanitizes all AI output before DOM injection
   - **Allowed Tags**: Limited to semantic HTML (h1-h6, p, lists, tables, emphasis, links)
   - **Allowed Attributes**: Only href, target, class, id
   - **No Scripts**: Event handlers and inline scripts blocked
   - **Fallback Safety**: Even plain text rendering routes through sanitizer

6. **RTL/LTR Support**:
   - Directional CSS rules for Arabic (RTL) and English (LTR)
   - Proper padding/margins for lists, blockquotes, tables
   - Adaptive text alignment based on language

**Benefits:**
- **Professional Presentation**: Consultations appear polished and easy to digest
- **Improved Readability**: Visual hierarchy through cards, grids, and color coding
- **User Engagement**: Interactive elements with hover effects and animations
- **Mobile Responsive**: All components adapt to smaller screens
- **Secure**: XSS protection ensures safe rendering of AI-generated content
- **Print-Ready**: Optimized CSS for printing consultation reports

**User Flow:**
1. AI generates consultation in Markdown format
2. JavaScript parses Markdown → HTML via Marked.js
3. DOMPurify sanitizes HTML (XSS protection)
4. JavaScript identifies patterns (lists, stats, grids)
5. Transforms patterns into visual components
6. Renders final formatted consultation with cards/tables/grids