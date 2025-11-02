# Mcidia Platform - Comprehensive Design Guidelines

## Design Approach

**Selected Approach**: Design System (Enterprise SaaS)  
**Rationale**: Mcidia is a complex, data-intensive B2B consulting platform with 12+ modules requiring consistency, scalability, and professional credibility. Drawing from enterprise systems like Salesforce, HubSpot, and Microsoft 365 while maintaining Arabic-first cultural sensitivity.

**Core Design Principles**:
- **Professional Authority**: Convey expertise and trustworthiness through refined, corporate aesthetics
- **Intelligent Clarity**: Make complex AI-powered insights digestible and actionable
- **Bilingual Excellence**: Seamless RTL/LTR experience without compromise
- **Purposeful Density**: Information-rich interfaces that don't overwhelm

---

## Color System

### Primary Palette
- **Primary**: `#0A2756` - Main navigation, headings, primary CTAs, logos
- **Secondary**: `#2C8C56` - Success states, positive metrics, feature highlights, confirmation buttons
- **Active UI**: `#2767B1` - Interactive elements, links, active states, hover effects
- **Background**: `#F7FBFF` - Page backgrounds, card surfaces

### Extended Palette
- **Text Primary**: `#0A2756` (high contrast for body text)
- **Text Secondary**: `#64748B` (supporting text, labels, metadata)
- **Text Muted**: `#94A3B8` (placeholders, disabled states)
- **Borders**: `#E2E8F0` (dividers, card borders, input fields)
- **Semantic Colors**:
  - Success: `#2C8C56`
  - Warning: `#F59E0B`
  - Error: `#EF4444`
  - Info: `#2767B1`

---

## Typography System

### Font Families
```
Arabic: 'Cairo', sans-serif (weights: 400, 500, 600, 700)
English: 'Poppins', sans-serif (weights: 400, 500, 600, 700)
```

### Type Scale
- **Display (Hero)**: 48px / 3rem, Bold (700), Line-height 1.2
- **H1 (Page Titles)**: 32px / 2rem, SemiBold (600), Line-height 1.3
- **H2 (Section Headers)**: 24px / 1.5rem, SemiBold (600), Line-height 1.4
- **H3 (Card Titles)**: 20px / 1.25rem, Medium (500), Line-height 1.5
- **Body Large**: 18px / 1.125rem, Regular (400), Line-height 1.6
- **Body Regular**: 16px / 1rem, Regular (400), Line-height 1.6
- **Body Small**: 14px / 0.875rem, Regular (400), Line-height 1.5
- **Caption**: 12px / 0.75rem, Regular (400), Line-height 1.4

---

## Layout System

### Spacing Scale (Tailwind Units)
**Primary Units**: 2, 4, 6, 8, 12, 16, 20, 24, 32
- Component padding: `p-6` or `p-8`
- Section spacing: `py-12` to `py-20`
- Card gaps: `gap-4` or `gap-6`
- Form fields: `space-y-4`

### Grid System
- **Dashboard Layouts**: 12-column grid with `gap-6`
- **Module Pages**: Sidebar (256px fixed) + Main content (flex-1)
- **Cards Grid**: 3 columns on lg (grid-cols-1 md:grid-cols-2 lg:grid-cols-3)
- **Data Tables**: Full-width with horizontal scroll on mobile

### Container Constraints
- **Max Width**: 1440px (max-w-7xl)
- **Content Width**: 1280px (max-w-6xl) for reading-heavy pages
- **Form Width**: 640px (max-w-2xl) for focused inputs

---

## Component Library

### Navigation
**Top Navigation Bar**:
- Fixed header, height 72px, background #FFFFFF, border-bottom #E2E8F0
- Logo (left/right based on language), centered search bar, profile/notifications (right/left)
- Language toggle, notification bell with badge counter
- Sticky on scroll with subtle shadow

**Sidebar Navigation** (Dashboard):
- Width 256px, background #FFFFFF, height 100vh, border-right/left #E2E8F0
- Module icons (24px) with labels, hover background #F7FBFF
- Active state: background #EBF5FF, left/right border 3px #2767B1
- Collapsible on mobile (hamburger menu)

### Cards
**Standard Card**:
- Background #FFFFFF, border-radius 12px, border 1px #E2E8F0
- Padding: p-6, subtle shadow: shadow-sm hover:shadow-md transition
- Header: Icon + Title (H3) + Optional Badge/Metric
- Body: Content with clear hierarchy
- Footer: Actions or metadata (text-sm text-secondary)

**Stat Card**:
- Large number (text-3xl font-bold #0A2756)
- Label below (text-sm text-secondary)
- Trend indicator (arrow + percentage in #2C8C56 or #EF4444)
- Small sparkline chart optional

**Feature Card** (Landing):
- Icon container (64px circle, background gradient #2767B1 to #2C8C56)
- Title (text-xl font-semibold)
- Description (2-3 lines, text-secondary)
- "Learn More" link (#2767B1)

### Buttons
**Primary Button**:
- Background #0A2756, text white, px-6 py-3, rounded-lg
- Hover: background #0D3168, transition 200ms
- Font: 16px medium (500)

**Secondary Button**:
- Background #2C8C56, text white, px-6 py-3, rounded-lg
- Hover: background #257A4A, transition 200ms

**Outline Button**:
- Border 2px #0A2756, text #0A2756, px-6 py-3, rounded-lg
- Hover: background #0A2756, text white

**Icon Button**:
- 40px square, rounded-lg, text #64748B
- Hover: background #F7FBFF

### Forms
**Input Fields**:
- Height 48px, px-4, rounded-lg, border 2px #E2E8F0
- Focus: border #2767B1, outline-none, shadow-sm
- Label above (text-sm font-medium #0A2756), margin-bottom mb-2
- Error state: border #EF4444, error message below (text-sm #EF4444)

**Select Dropdowns**:
- Same styling as inputs with chevron-down icon
- Dropdown menu: background #FFFFFF, shadow-lg, rounded-lg, max-height 256px

**Checkboxes/Radio**:
- Custom styled, 20px square/circle, border 2px #E2E8F0
- Checked: background #2767B1, white checkmark

### Data Display
**Tables**:
- Header: background #F7FBFF, text-sm font-semibold #0A2756, py-3 px-4
- Rows: border-bottom #E2E8F0, py-4 px-4, hover:background #F7FBFF
- Alternating rows optional for dense data
- Responsive: horizontal scroll on mobile

**Charts & Visualizations**:
- Use Chart.js or ApexCharts with brand colors
- Primary data: #2767B1, Secondary: #2C8C56, Additional: #F59E0B
- Clean grid lines (#E2E8F0), clear axis labels
- Interactive tooltips on hover

**Badges**:
- Small (px-3 py-1, text-xs, rounded-full)
- Colors based on status: Success (#2C8C56), Warning (#F59E0B), Error (#EF4444), Info (#2767B1)

### Modals & Overlays
**Modal Dialog**:
- Backdrop: rgba(10, 39, 86, 0.5)
- Container: max-width 600px, background #FFFFFF, rounded-xl, shadow-2xl
- Header: p-6, border-bottom #E2E8F0, close button
- Body: p-6
- Footer: p-6, border-top #E2E8F0, action buttons

**Toast Notifications**:
- Fixed position top-right/left, width 360px
- Background #FFFFFF, shadow-lg, rounded-lg, p-4
- Icon + Message + Close button, auto-dismiss 5s

---

## Page Templates

### Landing Page
**Hero Section** (100vh):
- Large hero image: Professional diverse business team in modern office (gradient overlay rgba(10, 39, 86, 0.7))
- Centered content: Logo, headline "منصة Mcidia الذكية", slogan, description
- Primary CTA "ابدأ الآن" (background #2C8C56) + Secondary "اكتشف الخدمات"
- Buttons with backdrop-blur-md background

**Services Grid** (py-20):
- 3-column grid of feature cards showcasing 12 modules
- Each card: Icon, title, 2-line description, hover lift effect

**Trust Section**:
- Stats row: 4 columns (Clients served, AI consultations, Success rate, Years experience)
- Client logos carousel (grayscale, color on hover)

**Pricing Section**:
- 3 pricing cards (Monthly, Yearly, Pay-per-Use)
- Highlighted "Most Popular" with scale-105 and shadow-xl
- Feature comparison table below

**Footer** (background #0A2756, text white):
- 4 columns: About, Services, Support, Contact
- Social icons, language toggle, copyright
- Newsletter signup form

### Dashboard
**Top Stats Row**:
- 4 stat cards: Active Projects, AI Credits Used, Performance Score, Pending Tasks

**Quick Access Grid**:
- 3x4 grid of module cards with icons and recent activity count
- Each card clickable to module

**Recent Activity Feed**:
- Timeline of AI consultations, report generations, team actions

**Charts Section**:
- 2-column: Usage trends (line chart) + Module distribution (donut chart)

### Module Pages (Strategy/HR/Finance/etc.)
**Page Header**:
- Breadcrumb navigation, page title (H1), description
- Primary action button ("إنشاء مشروع جديد")

**Content Area**:
- Left: Form/Input section (640px max-width), step-by-step wizard or single form
- Right: AI suggestions panel, help tips, recent projects list

**Results Display**:
- Generated content in rich text editor or downloadable PDF preview
- Edit/refine options, save to workspace

---

## Animations & Interactions

**Micro-interactions**:
- Button hover: subtle scale-105, transition 200ms
- Card hover: shadow elevation, transition 300ms
- Loading states: Spinner (border-t-4 #2767B1, animate-spin)

**Page Transitions**:
- Fade in content on load (opacity 0 to 1, duration 400ms)
- Avoid heavy animations, prioritize performance

---

## RTL/LTR Support

**Implementation**:
- Use `dir="rtl"` or `dir="ltr"` on `<html>` tag
- Mirror layouts: sidebar right/left, text-align right/left
- Flip icons directionally (arrows, chevrons)
- Use logical properties (start/end instead of left/right) in CSS
- Test all components in both directions

---

## Images

**Hero Image**: Professional consulting scene - diverse team collaborating in modern office with digital interfaces visible, corporate setting (1920x1080, high quality)

**Module Icons**: Use FontAwesome Pro or Heroicons for consistency (strategy: compass, HR: users, finance: chart-line, etc.)

**Illustrations**: Minimal line-art illustrations for empty states and onboarding, using brand colors

---

## Accessibility

- WCAG 2.1 AA compliance
- Color contrast ratios: 4.5:1 for body text, 3:1 for large text
- Keyboard navigation: visible focus states (outline 2px #2767B1, offset 2px)
- ARIA labels for icon-only buttons
- Semantic HTML structure (nav, main, section, article)