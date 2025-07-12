# Surfe Multi API - Supabase Edition

A comprehensive Flask web application that provides access to the Surfe API with intelligent key management, multi-user support, and monitoring capabilities powered by Supabase.

## 🚀 Features

### Core Functionality
- **People Search**: Advanced filtering by company, seniority, department, and location
- **People Enrichment**: Comprehensive data enhancement with professional details
- **Company Search**: Industry-based filtering with size and location options  
- **Company Enrichment**: Detailed company information including financials and tech stack
- **Bulk Operations**: CSV import/export for batch processing

### Enhanced API Management
- **Multi-User Support**: Each user manages their own API keys
- **Database-Backed Keys**: Persistent storage in Supabase
- **Key ID System**: Unique identifiers for each API key
- **Usage Tracking**: Per-key usage statistics and analytics
- **Row Level Security**: Data isolation between users
- **Real-time Monitoring**: Dashboard with health metrics and usage statistics

### New Supabase Features
- **User Context Management**: Automatic user session handling
- **API Request Logging**: Complete request/response tracking
- **Enhanced Security**: Service role key support for admin operations
- **Database Configuration**: Centralized config management
- **Automatic Sync**: Environment keys sync to database on startup

## 🛠️ Tech Stack

- **Backend**: Flask, Supabase Python Client
- **Database**: Supabase (PostgreSQL with built-in auth)
- **Frontend**: Bootstrap 5 Dark Theme, Vanilla JavaScript
- **API Client**: Async HTTP with Supabase key management
- **Authentication**: Session-based with user context decorators

## 📦 Installation

### Prerequisites
- Python 3.11+
- Supabase account and project
- Surfe API key(s)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/surfe-multi-api-supabase.git
cd surfe-multi-api-supabase
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Supabase**
```bash
# Create .env file with your credentials
cp .env.example .env
```

4. **Set environment variables**
```bash
# Flask Configuration
SESSION_SECRET=your-secret-key
FLASK_ENV=development
PORT=5000

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # Optional, for admin features

# API Configuration
MAX_API_KEYS_PER_USER=100

# Initial API Keys (optional)
SURFE_API_KEY_1=your-api-key-1
SURFE_API_KEY_2=your-api-key-2
```

5. **Initialize database tables**

Create these tables in your Supabase project:

```sql
-- Users table
CREATE TABLE users (
    email VARCHAR PRIMARY KEY,
    name VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- API Keys table
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR REFERENCES users(email),
    service VARCHAR DEFAULT 'surfe',
    api_key TEXT NOT NULL,
    key_name VARCHAR UNIQUE,
    is_active BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- API Requests logging table
CREATE TABLE api_requests (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR REFERENCES users(email),
    service VARCHAR,
    endpoint VARCHAR,
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    processing_time FLOAT,
    api_key_id INTEGER REFERENCES api_keys(id),
    api_key_name VARCHAR,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_api_keys_user ON api_keys(user_email);
CREATE INDEX idx_api_keys_active ON api_keys(user_email, is_active);
CREATE INDEX idx_api_requests_user ON api_requests(user_email);
```

6. **Run the application**
```bash
python app.py  # Or python main.py if using the existing entry point
```

The app will be available at `http://localhost:5000`

## 🌐 Deployment

### Vercel Deployment

This application supports Vercel deployment with Supabase:

1. **Deploy to Vercel**
```bash
vercel --prod
```

2. **Configure Environment Variables in Vercel Dashboard**
   - All Supabase credentials
   - Session secret
   - Initial API keys (optional)

3. **Database Setup**
   - Use Supabase dashboard to create tables
   - Enable Row Level Security if needed

## 📖 Usage

### User Context
The application automatically manages user context through session cookies and the `@set_user_context` decorator.

### API Key Management

**Adding Keys:**
- Environment keys are synced to database on startup
- Add new keys via Settings page web interface
- Each key gets a unique ID and standardized name

**Managing Keys:**
- **Select**: Choose active key for API requests
- **Enable/Disable**: Control key availability
- **Delete**: Remove keys (with proper permissions)
- **Test**: Validate key functionality

### Search & Enrichment

1. **People Search**: Filter by industry, seniority, department, location
2. **Company Search**: Find companies by industry, size, location
3. **Enrichment**: Upload CSV files or enter data manually
4. **Export**: Download results in CSV format

### API Endpoints

#### Health & Diagnostics
- `GET /health` - Health check with database status
- `GET /api/stats` - API usage statistics
- `GET /config-info` - Configuration details (dev only)

#### Settings & Key Management
- `POST /api/settings/add-api-key` - Add new API key
- `POST /api/settings/select-api-key` - Select active key
- `GET /api/settings/list-api-keys` - List user's keys
- `GET /api/settings/usage-stats` - Get usage statistics

## 📊 Monitoring

The enhanced dashboard provides:
- **Database Health**: Connection status and availability
- **User Statistics**: Per-user usage tracking
- **Key Analytics**: Individual key performance metrics
- **Request History**: Complete API request logging
- **Real-time Updates**: Auto-refreshing health indicators

## 🏗️ Project Structure

```
Surfe-Multi-API-supabase/
├── app.py                      # Main Flask application
├── app_old.py                  # Previous version 
├── routes.py                   # Centralized route definitions
├── main.py                     # Application entry point
├── setup.py                    # Setup configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── LICENSE                     # License file
├── pyproject                   # Project configuration
├── vercel.json                 # Vercel deployment config
├── VERCEL_DEPLOY               # Deployment instructions
├── global_error_fixer.py       # Error handling utility
├── repilt                      # Replit configuration
├── DEPLOYMENT                  # Deployment notes
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
│
├── api/                        # API route handlers
│   └── routes/
│       ├── __init__.py         # Routes module initialization
│       ├── auth.py        
│       ├── company_enrichment.py   # Company enrichment endpoints
│       ├── company_search.py       # Company search endpoints
│       ├── dashboard.py            # Dashboard and stats endpoints
│       ├── diagnostics.py          # Performance diagnostics
│       ├── people_enrichment.py    # People enrichment endpoints
│       ├── people_search.py        # People search endpoints
│       └── settings.py             # API key management endpoints
│
├── config/                     # Configuration management
│   ├── config.py              # General configuration
│   ├── database_config.py     # Database configuration
│   └── supabase_api_manager.py # API key management
│
├── core/                      # Core functionality
│   ├── __init__.py
│   ├── dependencies.py        # Decorators and dependencies
│   └── user_context.py        # User context management
│
├── database/                  # Database layer
│   └── supabase_client.py    # Supabase client wrapper
│
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── email_service.py
│   └── supabase_api_client.py # Surfe API client
├── static/                     # Frontend assets
│   ├── css/
│   │   ├── people_enrichment.css
│   │   └── styles.css
│   └── js/
│       ├── appState.js         # Application state management
│       ├── autocompletion.js   # Autocomplete functionality
│       ├── company_enrichment_v2.js    # Company enrichment logic
│       ├── company_enrichment.js       # Legacy company enrichment
│       ├── company_search.js           # Company search functionality
│       ├── dashboard.js                # Dashboard interactions
│       ├── people_enrichment_old.js    # Legacy people enrichment
│       ├── people_enrichment_utils.js  # People enrichment utilities
│       ├── people_enrichment.js        # People enrichment logic
│       ├── people_search.js            # People search functionality
│       ├── settings.js                 # Settings page logic
│       └── shared.js                   # Shared utilities
│
├── templates/                  # HTML templates
│   ├──emails/                  # Email templates
│   │  ├── base_email.html
│   │  ├── password_reset.html
│   │  └── welcome.html
│   ├── base.html               # Base template with common layout
│   ├── company_enrichment.html # Company enrichment page
│   ├── company_search.html     # Company search page
│   ├── dashboard.html          # Dashboard/home page
│   ├── homepage.html           # Home page
│   ├── diagnostics.html        # Diagnostics page
│   ├── forgot_password.html
│   ├── reset_password.html
│   ├── login.html
│   ├── people_enrichment.html  # People enrichment page
│   ├── people_search.html      # People search page
│   └── settings.html           # Settings/API key management
├── testing/                    # Test files
└── instance/                   # Instance-specific files

```

## Key Components

### 1. **Main Application (`app.py`)**
- Flask app initialization
- CORS configuration
- Database availability checking
- Initial sync of environment keys to database

### 2. **Route Management (`routes.py`)** *(NEW)*
- Centralized route definitions
- Separates routing logic from app configuration
- Includes all API endpoints and page routes

### 3. **API Routes (`api/routes/`)**
Contains the business logic for each endpoint group:

- **`dashboard.py`**: Health checks, API statistics
- **`settings.py`**: API key CRUD operations
- **`people_search.py`**: People search functionality
- **`company_search.py`**: Company search functionality
- **`people_enrichment.py`**: People data enrichment
- **`company_enrichment.py`**: Company data enrichment
- **`diagnostics.py`**: Performance metrics and diagnostics

### 4. **Database Layer (`database/`)**
- **`supabase_client.py`**: Wrapper for Supabase operations
  - API key management (CRUD)
  - User management
  - Usage tracking and logging
  - RLS (Row Level Security) support

### 5. **Configuration (`config/`)**
- **`database_config.py`**: Database configuration management
- **`supabase_api_manager.py`**: API key lifecycle management
- **`config.py`**: General app configuration

### 6. **Core Functionality (`core/`)**
- **`dependencies.py`**: Decorators like `@set_user_context`
- **`user_context.py`**: User session management

### 7. **Utilities (`utils/`)**
- **`supabase_api_client.py`**: Surfe API client implementation
  - Handles API requests with Supabase-managed keys
  - Domain cleaning and validation
  - Request logging

## API Endpoints

### Health & Diagnostics
- `GET /health` - Health check
- `GET /api/health` - API health check (duplicate)
- `GET /api/stats` - API statistics
- `GET /api/diagnostics/performance` - Performance metrics

### People Operations
- `POST /api/v2/people/search` - Search for people
- `POST /api/v2/people/enrich` - Enrich single person
- `POST /api/v2/people/enrich/bulk` - Bulk enrichment
- `GET /api/v2/people/enrich/status/<id>` - Check enrichment status
- `GET /api/v2/people/enrich/combinations` - Get enrichment combinations

### Company Operations
- `POST /api/v2/companies/search` - Search for companies
- `POST /api/v2/companies/enrich` - Enrich single company
- `POST /api/v2/companies/enrich/bulk` - Bulk enrichment
- `GET /api/v2/companies/enrich/status/<id>` - Check enrichment status

### Settings & API Key Management
- `GET /api/settings/config` - Get settings configuration
- `POST /api/settings/keys` - Add new API key
- `DELETE /api/settings/keys` - Remove API key
- `POST /api/settings/keys/status` - Update key status
- `POST /api/settings/select` - Select active API key
- `POST /api/settings/test` - Test selected API key
- `POST /api/settings/refresh` - Refresh API keys

### Enhanced Settings (if DATABASE_CONFIG_AVAILABLE)
- `POST /api/settings/add-api-key` - Add API key (enhanced)
- `POST /api/settings/remove-api-key` - Remove API key (enhanced)
- `POST /api/settings/select-api-key` - Select API key (enhanced)
- `POST /api/settings/enable-api-key` - Enable API key
- `POST /api/settings/disable-api-key` - Disable API key
- `POST /api/settings/test-api-key` - Test API key (enhanced)
- `GET /api/settings/list-api-keys` - List all user's API keys
- `GET /api/settings/current-user` - Get current user info
- `GET /api/settings/usage-stats` - Get API usage statistics

### Web Pages
- `GET /` - Dashboard
- `GET /people-search` - People search page
- `GET /company-search` - Company search page
- `GET /people-enrichment` - People enrichment page
- `GET /company-enrichment` - Company enrichment page
- `GET /diagnostics` - Diagnostics page
- `GET /settings` - Settings page

## Features

### Multi-User Support
- User context management via decorators
- Row Level Security (RLS) in Supabase
- Per-user API key management

### API Key Management
- Store multiple API keys per user
- Select active key for requests
- Track usage per key
- Enable/disable keys
- Test key validity

### Request Tracking
- Log all API requests
- Track response times
- Monitor status codes
- Usage statistics per key

### Database Integration
- Supabase for data persistence
- Automatic sync of environment keys
- Support for both anon and service role keys

## Environment Variables

```bash
# Flask Configuration
SESSION_SECRET=your-secret-key
FLASK_ENV=development|production
PORT=5000

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Configuration
MAX_API_KEYS_PER_USER=100

# Initial API Keys (optional)
SURFE_API_KEY_1=your-api-key-1
SURFE_API_KEY_2=your-api-key-2
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SURFE-MULTI-API-SUPABASE
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Fill in your Supabase credentials
   - Add any initial API keys

4. **Initialize database**
   - Ensure Supabase tables are created
   - Run the app to sync initial keys

5. **Run the application**
   ```bash
   python app.py
   ```

## Development

### Adding New Routes
1. Define the route handler in appropriate file under `api/routes/`
2. Add the route definition to `routes.py`
3. Apply necessary decorators (`@set_user_context`)

### Database Schema
The application expects these Supabase tables:
- `users` - User profiles
- `api_keys` - API key storage
- `api_requests` - Request logging

### Testing
Run tests from the `testing/` directory:
```bash
python -m pytest testing/
```

## Security Considerations

- API keys are stored encrypted in Supabase
- Row Level Security (RLS) ensures data isolation
- User context is validated on each request
- Service role key is only used for admin operations

## 🔒 Security Features

- **Row Level Security**: User data isolation in Supabase
- **Session Management**: Secure cookie-based sessions
- **API Key Encryption**: Stored securely in database
- **User Context Validation**: Every request is authenticated
- **Admin Role Separation**: Service role key for privileged operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Surfe API Documentation](https://api.surfe.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Vercel Deployment Guide](VERCEL_DEPLOY.md)

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

Built with ❤️ for efficient people and company data enrichment, powered by Supabase for scalable multi-user support.