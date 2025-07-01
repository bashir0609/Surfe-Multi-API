# Surfe Multi API

## Overview

This is a Flask-based web application that serves as a frontend for the Surfe API, providing people and company search capabilities with intelligent API key rotation and comprehensive monitoring. The application features a dashboard for monitoring API usage, separate search interfaces for people and companies, and a robust API key management system designed to handle rate limiting and quota exhaustion.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with full ACID compliance and connection pooling
- **API Client**: Custom async HTTP client with automatic key rotation
- **Authentication**: Environment-based API key management
- **Middleware**: ProxyFix for reverse proxy compatibility

### Frontend Architecture
- **Template Engine**: Jinja2 with Bootstrap 5 Dark Theme
- **JavaScript**: Vanilla JS with modular architecture
- **Styling**: Custom CSS with Bootstrap integration
- **Icons**: Font Awesome for UI consistency

### Database Schema
The application uses two main models:
- `ApiRequest`: Tracks all API requests for analytics (endpoint, method, status, response time)
- `ApiKeyMetrics`: Monitors API key performance and health (usage counts, success rates, last used timestamps)

## Key Components

### Simple API Key Management System
- **SimpleApiManager**: Loads API keys from Vercel environment variables
- **Key Selection**: Users can select which API key to use for all requests
- **Enable/Disable**: Individual keys can be enabled or disabled
- **Environment Integration**: Automatically discovers keys from SURFE_API_KEY, SURFE_API_KEY_1, etc.

### Search Modules
- **People Search**: Advanced filtering by company, seniority, department, location
- **Company Search**: Industry-based filtering with company size and location options
- **Real-time Results**: Async processing with loading indicators and error handling

### Monitoring Dashboard
- **Key Metrics**: Real-time statistics on API key health and usage
- **Request Analytics**: Historical data on API performance
- **Health Checks**: System status monitoring with automatic refresh
- **Export Capabilities**: Data export for external analysis

### Core Services
- **Request Validation**: Input sanitization and structure validation
- **Error Handling**: Comprehensive error logging and user-friendly error messages
- **Configuration Management**: Environment-based configuration with multiple fallback methods

## Data Flow

1. **Request Initiation**: User submits search form through web interface
2. **Data Validation**: Server validates request structure and required fields
3. **API Key Selection**: Rotation system selects next available healthy API key
4. **External API Call**: Async HTTP request to Surfe API with retry logic
5. **Response Processing**: Data transformation and error handling
6. **Metrics Recording**: Request analytics stored in database
7. **Client Response**: JSON data returned to frontend for display

## External Dependencies

### Required Services
- **Surfe API**: External service for people and company data
- **API Keys**: Multiple Surfe API keys for rotation (configured via environment variables)

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: No framework dependencies for lightweight performance

### Python Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **aiohttp**: Async HTTP client for external API calls
- **Werkzeug**: WSGI utilities and middleware

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with debug logging
- **Production**: PostgreSQL support with ProxyFix middleware
- **API Keys**: Multiple environment variable patterns supported
- **Session Management**: Configurable secret keys

### Database Setup
- **PostgreSQL Integration**: Full production-ready database with automatic table creation
- **Auto-migration**: Tables created automatically on startup with proper schema
- **Health Monitoring**: Built-in database connectivity checks and connection validation
- **Connection Pooling**: Configured for production reliability with pool_recycle and pool_pre_ping
- **ACID Compliance**: Full transactional support for data consistency

### Monitoring and Logging
- **Request Tracking**: All API calls logged with performance metrics
- **Error Logging**: Comprehensive error tracking and debugging
- **Health Endpoints**: Built-in health check routes for monitoring

## Changelog
- June 30, 2025: Initial setup with Flask backend and API rotation system
- June 30, 2025: Added all 4 core functions (people search, people enrichment, company search, company enrichment)
- June 30, 2025: Integrated PostgreSQL database with automatic table creation and connection pooling
- June 30, 2025: Enhanced navigation with dropdown menus and comprehensive UI for all features
- June 30, 2025: Completed web-based API key management system with dynamic key addition, validation, and real-time dashboard updates
- July 1, 2025: Enhanced People Search with comprehensive Surfe API v2 field support including domain include/exclude with CSV upload, company/people country filtering, employee count ranges, revenue ranges, and proper API field mapping
- July 1, 2025: Successfully integrated authentic autocomplete data from official Surfe API documentation - console logs confirm real seniorities (Board Member, C-Level, Founder), departments (Accounting and Finance, Engineering), industries (3D Technology, Artificial Intelligence), and ISO 3166-1 country codes are loading correctly. Ready for Vercel deployment with vercel.json configuration and Vercel Postgres database support.
- July 1, 2025: Replaced complex API key rotation system with simplified environment-based key management. API keys now retrieved from Vercel environment variables (SURFE_API_KEY, SURFE_API_KEY_1, etc.) with enable/disable/select functionality. Removed rotation complexity and implemented simple key selection system for improved user control.
- July 1, 2025: Completed removal of API key rotation system. All API routes now use simplified client (utils/simple_api_client.py) with single selected key approach. Hybrid system supports both environment variables from Vercel and dynamic key addition through web interface. Settings page includes remove functionality for dynamic keys while protecting environment keys.
- July 1, 2025: Fixed company search autocomplete functionality by adding authentic Surfe API data to global SurfeApp.data object. All pages now use consistent authentic data from shared.js instead of static arrays. 
- July 1, 2025: **COMPLETED**: Total removal of ALL API rotation terminology from entire application. Replaced "API Rotation Enabled" badges with "Simple Key Selection", updated all page headers, comments, function names, and variable references. Application now consistently uses selected key system throughout all 5+ pages (dashboard, people search, people enrichment, company search, company enrichment, settings, diagnostics).
- July 1, 2025: **COMPLETED**: Total removal of ALL auto-retry functionality from entire application. Removed retry loops, retry counters, retry delays, and retry buttons. API client now makes single attempts only. Changed "Retry" buttons to "Try Again" and "Reload" for better user experience. Simplified configuration to use single request attempts.
- July 1, 2025: **COMPLETED**: JavaScript code consolidation and optimization. Moved repetitive utility functions to shared.js: parseTextareaLines(), isValidUrl(), isValidEmail(), isValidDomain(), formatLargeNumber(), formatRevenue(), truncateText(), resetForm(), updateButtonState(), and sanitizeHtml(). Updated all modules (people_enrichment.js, company_enrichment.js, company_search_v2.js) to use shared utilities. Removed backup JavaScript files and duplicate function definitions. Improved code maintainability and reduced duplication across the application.
- July 1, 2025: **COMPLETED**: CSS consolidation and inline style elimination. Moved all inline styles to centralized styles.css utility classes including: .hidden/.visible for display control, .z-index-toast for toast positioning, .scroll-area for scrollable containers, and .d-flex-center for flex layouts. Updated all templates (settings.html, diagnostics.html, base.html) to use CSS classes instead of style attributes. Enhanced shared.js with show(), hide(), and toggle() utility functions for consistent element visibility management. Improved maintainability by eliminating inline styles across the entire application.
- July 1, 2025: **COMPLETED**: CSV functionality consolidation. Moved all CSV-related functions to shared.js utilities including: exportToCsv(), exportToJson(), convertToCSV(), parseCSV(), validateCSVFile(), readCSVFile(), and downloadFile(). Updated all modules (people_enrichment.js, company_enrichment.js, company_search_v2.js) to use centralized CSV utilities instead of scattered implementations. Enhanced file validation with comprehensive error handling and proper CSV parsing with quote escaping. Standardized export functionality across all features for consistent user experience.
- July 1, 2025: **COMPLETED**: Autocompletion functionality consolidation. Created dedicated autocompletion.js module with centralized form population functions: populateSelect(), populateMultipleSelects(), populatePeopleSearchForm(), populateCompanySearchForm(). Updated all search modules to use centralized autocomplete with fallback support. Added auto-detection functionality and utility functions for select management. All forms now use consistent autocomplete implementation with proper authentic data integration.
- July 1, 2025: **COMPLETED**: Created improved People Search v2 and Company Search v2 pages with better field sizing, responsive layouts, and enhanced autocomplete integration. Built corresponding JavaScript modules (people_search_v2.js, company_search_v3.js) with proper API endpoint mapping. Added Flask routes for /people-search-v2 and /company-search-v2. Updated navigation to use v2 pages. Fixed API endpoints and integrated complete authentic Surfe industry list with hundreds of real industry options from official API documentation.
- July 1, 2025: **COMPLETED**: Converted autocomplete fields to searchable input boxes using HTML5 datalist elements. Users can now type to search through authentic data instead of scrolling through dropdown lists. Updated autocompletion.js with populateDatalist() function and modified both search forms to use input fields with datalist suggestions.
- July 1, 2025: **COMPLETED**: Enhanced Company Search with missing authentic Surfe API v2 filters. Added domains/domainsExcluded arrays, employeeCount/revenue range objects, proper countries arrays, and pageToken pagination. Updated backend to use Surfe API v2 endpoint (/v2/companies/search) and restructured JavaScript to build authentic API request format matching official Surfe documentation.
- July 1, 2025: **COMPLETED**: Added comprehensive CSV functionality with column selection to both Company Search and People Search. Users can upload CSV files, select which column contains domains, and the system extracts and adds those domains to filtering. Fixed CSV parsing errors and implemented proper FileReader handling with column dropdown population. Both search pages now have identical CSV upload capabilities with tab-based include/exclude domain management.
- July 1, 2025: **COMPLETED**: Updated People Enrichment to comply with authentic Surfe API v2 structure. Added include configuration options (email, linkedInUrl, mobile), restructured people objects with proper fields (firstName, lastName, companyName, companyDomain, linkedinUrl, externalID), and updated both frontend form and backend API handling to match official Surfe API v2 enrichment format exactly.
- July 1, 2025: **COMPLETED**: Enhanced People Enrichment with comprehensive user-facing validation requirements display. Added requirement information boxes throughout all input methods (manual, CSV, bulk) explaining person identification needs, field character limits (2000 chars), array size limits (1-10000 people), include field requirements, and notificationOptions with webhook URL support. Users now have clear guidance for successful API compliance.
- July 1, 2025: **COMPLETED**: Updated People Search to comply with authentic Surfe API v2 specification. Restructured JavaScript to build proper nested API request format with companies/people objects, added missing fields (jobTitles array, correct domain field names), fixed peoplePerCompany limits (1-5), updated limit range (1-200), corrected field names (from/to for ranges), and updated response handling to match API structure. Added comprehensive requirement information for users explaining search filter requirements.
- July 1, 2025: **COMPLETED**: Enhanced People Search form organization and domain limit documentation. Separated People Filters and Company Filters into distinct visual sections with color-coded icons and clear section headers. Added comprehensive domain limit information (max 10,000 domains for both include/exclude lists) with warning alerts and form field hints. Fixed seniority autocomplete functionality and improved overall form usability with better field grouping.
- July 1, 2025: **COMPLETED**: Updated Company Enrichment to comply with authentic Surfe API v2 specification. Restructured both frontend and backend to use companies array with required domain and optional externalID fields. Simplified manual form to focus on API requirements, updated bulk form with domain/external ID pairing, modified CSV processing to handle new structure, and added comprehensive API v2 compliance notices throughout the interface. All Company Enrichment methods now use authentic API structure.
- July 1, 2025: **COMPLETED**: Fixed critical JavaScript API function call bugs that were preventing enrichment functionality. Corrected `SurfeApp.api.makeRequest()` calls to use proper `SurfeApp.api.request()` method name. Applied domain validation fixes to all enrichment pages (people and company enrichment) with comprehensive domain cleaning on both frontend and backend. Fixed People Search results display by updating field mapping to handle multiple API response formats (firstName/first_name, companyName/company_name, jobTitle/job_title, linkedinUrl/linkedin_url).
- July 1, 2025: **COMPLETED**: Enhanced all search and enrichment result displays across the entire application. Updated People Search, Company Search, People Enrichment, and Company Enrichment to show comprehensive data including email, phone, location, country, seniority, department, company domain, founded year, funding stage, technologies, and more. Added debug logging to display actual API response data structure. Improved card layouts with better organization, icons, and action buttons. All pages now handle multiple field name formats from API responses and display rich, detailed information instead of basic name/title/company only.
- July 1, 2025: **COMPLETED**: Fixed auto-refresh system to be disabled by default and only run when manually enabled. Removed automatic health check requests that were running on all pages. Added optional auto-refresh toggle on settings page for users who want real-time API key monitoring. Auto-refresh now properly stops when navigating away or switching tabs. This eliminates unnecessary background API requests and improves performance.

## User Preferences

Preferred communication style: Simple, everyday language.