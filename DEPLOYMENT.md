# Deployment Guide

## GitHub Repository Setup

### 1. Create GitHub Repository
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: Surfe Multi API"

# Add remote origin (replace with your repository URL)
git remote add origin https://github.com/yourusername/surfe-api-web-app.git
git branch -M main
git push -u origin main
```

### 2. Environment Configuration

Create a `.env` file for local development:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/surfe_api
SESSION_SECRET=your-very-secure-session-secret-key-here
```

## Deployment Options

### Option 1: Replit Deployment

1. **Connect GitHub to Replit**:
   - Go to Replit.com
   - Click "Create Repl" → "Import from GitHub"
   - Enter your repository URL
   - Choose "Python" as the language

2. **Configure Environment Variables**:
   - Go to "Secrets" tab in Replit
   - Add these variables:
     ```
     DATABASE_URL=<your-postgresql-url>
     SESSION_SECRET=<your-session-secret>
     ```

3. **Deploy**:
   - Click the "Deploy" button
   - Choose "Autoscale" deployment
   - Your app will be available at `<your-repl-name>.replit.app`

### Option 2: Railway Deployment

1. **Connect GitHub to Railway**:
   - Go to Railway.app
   - Click "Deploy from GitHub repo"
   - Select your repository

2. **Add PostgreSQL**:
   - Click "Add Service" → "Database" → "PostgreSQL"
   - Railway will provide `DATABASE_URL` automatically

3. **Set Environment Variables**:
   - Go to your service settings
   - Add `SESSION_SECRET` variable

4. **Deploy**:
   - Railway auto-deploys on git push
   - Access via provided Railway domain

### Option 3: Heroku Deployment

1. **Install Heroku CLI** and login:
   ```bash
   heroku login
   ```

2. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set SESSION_SECRET=your-session-secret
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Option 4: Docker Deployment

1. **Using Docker Compose** (includes PostgreSQL):
   ```bash
   docker-compose up -d
   ```

2. **Using Docker only**:
   ```bash
   # Build image
   docker build -t surfe-api-app .
   
   # Run with external database
   docker run -d \
     -p 5000:5000 \
     -e DATABASE_URL=your-postgresql-url \
     -e SESSION_SECRET=your-session-secret \
     surfe-api-app
   ```

### Option 5: VPS/Cloud Server

1. **Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip postgresql nginx
   ```

2. **Setup PostgreSQL**:
   ```bash
   sudo -u postgres createdb surfe_api
   sudo -u postgres createuser --superuser surfe_user
   ```

3. **Clone and Setup**:
   ```bash
   git clone https://github.com/yourusername/surfe-api-web-app.git
   cd surfe-api-web-app
   pip install -e .
   ```

4. **Configure Nginx** (optional):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Run with Systemd**:
   ```bash
   # Create service file
   sudo tee /etc/systemd/system/surfe-api.service > /dev/null <<EOF
   [Unit]
   Description=Surfe API Web App
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/surfe-api-web-app
   Environment=DATABASE_URL=postgresql://surfe_user@localhost/surfe_api
   Environment=SESSION_SECRET=your-session-secret
   ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:5000 main:app
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   sudo systemctl enable surfe-api
   sudo systemctl start surfe-api
   ```

## Post-Deployment Setup

### 1. Add API Keys
- Navigate to `/settings` on your deployed app
- Add your Surfe API keys using the web interface
- Test the keys using the "Test" button

### 2. Verify Functionality
- Test all 4 core functions:
  - People Search
  - People Enrichment  
  - Company Search
  - Company Enrichment
- Check the Dashboard for system health
- Verify CSV import/export functionality

### 3. Monitoring
- Monitor the `/api/health` endpoint
- Check `/api/stats` for usage analytics
- Set up alerts for API key failures

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SESSION_SECRET` | Flask session secret (generate strong key) | `your-256-bit-secret-key` |
| `SURFE_API_KEY` | Primary Surfe API key (optional) | `sk_live_...` |
| `SURFE_API_KEY_1` | Multiple keys for rotation (optional) | `sk_live_...` |

## Security Considerations

1. **Use HTTPS** in production
2. **Secure your SESSION_SECRET** - generate a cryptographically strong key
3. **Restrict database access** - use connection limits and firewall rules
4. **Keep dependencies updated** - regularly update packages
5. **Monitor API usage** - watch for unusual patterns

## Troubleshooting

### Common Deployment Issues

1. **Database Connection Failures**:
   - Verify `DATABASE_URL` format
   - Check network connectivity
   - Ensure PostgreSQL is running

2. **Application Won't Start**:
   - Check Python version (requires 3.11+)
   - Verify all dependencies are installed
   - Check application logs

3. **API Keys Not Working**:
   - Ensure keys are added via Settings page
   - Verify Surfe API quota and permissions
   - Check key rotation status

### Getting Support

1. Check application logs for detailed error messages
2. Verify environment variables are correctly set
3. Test database connectivity independently
4. Review the troubleshooting section in README.md