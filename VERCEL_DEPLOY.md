# Vercel Deployment Guide

## Prerequisites
1. Vercel account
2. Vercel Postgres database (as shown in your screenshot)
3. Surfe API keys

## Deployment Steps

### 1. Connect to Vercel
```bash
# If using Vercel CLI (optional)
npm i -g vercel
vercel login
vercel
```

### 2. Environment Variables
Set these in your Vercel project settings:

**Required:**
- `DATABASE_URL` - Your Vercel Postgres connection string
- `SESSION_SECRET` - Any secure random string
- `SURFE_API_KEY_1` - Your first Surfe API key
- `SURFE_API_KEY_2` - Your second Surfe API key (optional)
- `SURFE_API_KEY_3` - Your third Surfe API key (optional)

**From Vercel Postgres:**
- `POSTGRES_URL`
- `POSTGRES_PRISMA_URL`
- `POSTGRES_URL_NO_SSL`
- `POSTGRES_URL_NON_POOLING`
- `POSTGRES_USER`
- `POSTGRES_HOST`
- `POSTGRES_PASSWORD`
- `POSTGRES_DATABASE`

### 3. Database Setup
Your Vercel Postgres database will be automatically connected. The app will create tables on first run.

### 4. Deploy
1. Push to GitHub
2. Connect repository to Vercel
3. Deploy automatically

## Configuration Files
- `vercel.json` - Vercel deployment configuration
- `requirements_vercel.txt` - Python dependencies
- All Flask routes and static files are configured

## Features Included
- ✅ People Search with authentic Surfe API data
- ✅ People Enrichment
- ✅ Company Search  
- ✅ Company Enrichment
- ✅ API Key Management
- ✅ PostgreSQL Integration
- ✅ Real-time Dashboard
- ✅ CSV Import/Export

## Post-Deployment
1. Add your Surfe API keys via Settings page
2. Test all 4 core functions
3. The authentic autocomplete data will load fresh (no browser cache issues)