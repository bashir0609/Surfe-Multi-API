# Contributing to Surfe Multi API

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- Git

### Local Development
1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/surfe-api-web-app.git
   cd surfe-api-web-app
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Set up environment variables:
   ```bash
   export DATABASE_URL="postgresql://localhost/surfe_api_dev"
   export SESSION_SECRET="dev-secret-key"
   ```

5. Run the application:
   ```bash
   python main.py
   ```

## Making Changes

### Code Style
- Follow PEP 8 conventions
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and small

### Frontend Guidelines
- Use Bootstrap 5 classes for styling
- Maintain dark theme consistency
- Write modular JavaScript in separate files
- Follow the existing naming conventions

### Backend Guidelines
- Use Flask blueprints for route organization
- Handle errors gracefully with proper HTTP status codes
- Log important operations and errors
- Validate all user inputs

## Testing
- Add tests for new functionality
- Ensure existing tests pass
- Test both success and failure scenarios
- Verify API key rotation functionality

## Pull Request Process
1. Create a feature branch from main
2. Make your changes
3. Test thoroughly
4. Update documentation if needed
5. Submit pull request with clear description

## Bug Reports
Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error messages/logs
- Screenshots if applicable

## Feature Requests
Provide:
- Clear description of the feature
- Use case and benefits
- Proposed implementation approach
- Any relevant examples