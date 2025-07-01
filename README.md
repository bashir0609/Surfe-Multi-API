# Surfe Multi API

A comprehensive Flask web application that provides access to the Surfe API with intelligent key management and monitoring capabilities.

## 🚀 Features

### Core Functionality
- **People Search**: Advanced filtering by company, seniority, department, and location
- **People Enrichment**: Comprehensive data enhancement with professional details
- **Company Search**: Industry-based filtering with size and location options  
- **Company Enrichment**: Detailed company information including financials and tech stack

### API Management
- **Hybrid Key System**: Supports both environment variables and dynamic key addition
- **Simple Management**: Select, enable, disable API keys through web interface
- **Real-time Monitoring**: Dashboard with health metrics and usage statistics

### Data Features
- **CSV Import/Export**: Bulk operations with file upload support
- **Authentic Autocomplete**: Real Surfe API data for dropdowns and filters
- **Advanced Filtering**: Employee count ranges, revenue filters, country selection

## 🛠️ Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5 Dark Theme, Vanilla JavaScript
- **API Client**: Async HTTP with proper error handling
- **Database**: PostgreSQL with connection pooling

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Surfe API key(s)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/surfe-multi-api.git
cd surfe-multi-api
```

2. **Install dependencies**
```bash
pip install -r requirements_github.txt
```

3. **Set environment variables**
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/surfe_db"
export SURFE_API_KEY="your_surfe_api_key_here"
# Optional: Add multiple keys
export SURFE_API_KEY_1="key1"
export SURFE_API_KEY_2="key2"
```

4. **Run the application**
```bash
python main.py
```

The app will be available at `http://localhost:5000`

## 🌐 Deployment

### Vercel Deployment

This application is optimized for Vercel deployment with PostgreSQL:

1. **Deploy to Vercel**
```bash
vercel --prod
```

2. **Configure Environment Variables**
   - Add `SURFE_API_KEY` (or `SURFE_API_KEY_1`, `SURFE_API_KEY_2`, etc.)
   - Connect Vercel Postgres database (automatically sets `DATABASE_URL`)

3. **Database Setup**
   - Tables are created automatically on first run
   - No manual migration needed

## 📖 Usage

### Adding API Keys

**Environment Method:**
- Set `SURFE_API_KEY`, `SURFE_API_KEY_1`, etc. in your environment
- Keys are automatically discovered and loaded

**Web Interface Method:**
- Go to Settings page
- Use "Add API Key" form
- Keys are saved for the session

### API Key Management

- **Select**: Choose which key to use for all requests
- **Enable/Disable**: Control key availability
- **Remove**: Delete dynamically added keys (environment keys are protected)

### Search & Enrichment

1. **People Search**: Filter by industry, seniority, department, location
2. **Company Search**: Find companies by industry, size, location
3. **Enrichment**: Upload CSV files or enter data manually
4. **Export**: Download results in CSV format

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SURFE_API_KEY` | Primary Surfe API key | Yes* |
| `SURFE_API_KEY_1` | Additional API key | No |
| `SURFE_API_KEY_2` | Additional API key | No |
| `SESSION_SECRET` | Flask session secret | No |

*At least one API key is required (can be added via web interface)

### Database Schema

The application uses two main models:
- `ApiRequest`: Tracks API usage and performance
- `ApiKeyMetrics`: Monitors key health and statistics

## 📊 Monitoring

The dashboard provides:
- **System Health**: Percentage of enabled API keys
- **Usage Statistics**: Request counts and success rates
- **Key Status**: Individual key performance metrics
- **Real-time Updates**: Auto-refreshing health indicators

## 🏗️ Architecture

### Backend Architecture
- **Flask**: Web framework with SQLAlchemy ORM
- **PostgreSQL**: Production database with connection pooling
- **Simple API Client**: Selected key approach (no rotation complexity)
- **Middleware**: ProxyFix for reverse proxy compatibility

### Frontend Architecture
- **Bootstrap 5**: Dark theme UI framework
- **Vanilla JavaScript**: Modular architecture with no framework dependencies
- **Real-time Updates**: WebSocket-free auto-refresh system

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
- [Vercel Deployment Guide](VERCEL_DEPLOY.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 📞 Support

For support, please open an issue on GitHub or contact the development team.

---

Built with ❤️ for efficient people and company data enrichment.