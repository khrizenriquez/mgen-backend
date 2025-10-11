# Railway Deployment Setup

This guide helps you configure your Railway deployment correctly to resolve the configuration issues.

## 🚨 Critical Issues Fixed

The application was failing to start due to two critical configuration issues:

1. **DATABASE_URL not detected**: Railway automatically provides `DATABASE_URL` when PostgreSQL is attached, but our configuration was conflicting with this.
2. **DEFAULT_USER_PASSWORD configured in production**: This development-only variable was being set when it should not be in production.

## ✅ Solutions Implemented

### 1. Automatic DATABASE_URL Detection
- Removed explicit `DATABASE_URL` configuration from `railway.toml`
- Railway now provides `DATABASE_URL` automatically when PostgreSQL is attached
- Added database connection pool settings for production

### 2. Production Environment Validation
- Enhanced configuration validation with debugging output
- Added environment diagnostic script for troubleshooting
- Production startup script with automatic validation

### 3. Railway Configuration
Updated `railway.toml` with proper production settings:
```toml
[environments.production]
# Railway automatically provides DATABASE_URL when PostgreSQL is attached

# Database Configuration
DB_POOL_SIZE = "20"
DB_MAX_OVERFLOW = "30"
SQL_ECHO = "false"

# Application Configuration
ENVIRONMENT = "production"
DEBUG = "false"
```

## 🚀 Deployment Steps

### Step 1: Attach PostgreSQL Database
1. Go to your Railway project dashboard
2. Click "Add Plugin" → "PostgreSQL"
3. Railway will automatically create and attach the database
4. **Important**: Railway will automatically set the `DATABASE_URL` environment variable

### Step 2: Configure Secrets
Set these secrets in Railway (Project Settings → Variables):

#### Required Secrets
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secure-random-jwt-key-here

# Email Configuration (Mailjet)
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_API_SECRET=your-mailjet-api-secret
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your App Name
FRONTEND_URL=https://your-frontend-domain.com

# CORS Configuration
ALLOWED_ORIGINS=https://your-frontend-domain.com

# Monitoring (Grafana)
GRAFANA_ADMIN_USER=your-admin-username
GRAFANA_ADMIN_PASSWORD=your-secure-grafana-password
```

### Step 3: Remove Conflicting Variables
**CRITICAL**: Ensure these variables are NOT set in Railway:

- ❌ `DEFAULT_USER_PASSWORD` - **Must not be set in production**
- ❌ `DATABASE_URL` - **Let Railway set this automatically**

### Step 4: Deploy
```bash
# From your feature branch
git checkout feature/fix-production-config
git push origin feature/fix-production-config

# Create a Pull Request to merge into develop
# Then promote to stage and finally to main for production
```

## 🔍 Troubleshooting

### If Deployment Still Fails

1. **Check Railway Logs**: Look for the diagnostic output that shows all environment variables
2. **Verify DATABASE_URL**: The diagnostic will show if `DATABASE_URL` is configured and its format
3. **Check for DEFAULT_USER_PASSWORD**: The diagnostic will alert if this forbidden variable is set

### Common Issues

#### Issue: `DATABASE_URL: Required for database connection - NOT SET`
**Solution**: Ensure PostgreSQL is properly attached to your Railway project. Railway should automatically provide this variable.

#### Issue: `DEFAULT_USER_PASSWORD: Should not be set in production`
**Solution**: Remove this variable from Railway environment variables. It's only for development.

#### Issue: Application starts but can't connect to database
**Solution**: Check that the `DATABASE_URL` format is correct. It should look like:
```
postgresql://username:password@host:port/database
```

## 📋 Environment Variables Checklist

### ✅ Automatically Provided by Railway
- `DATABASE_URL` (when PostgreSQL is attached)
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT_ID`
- `RAILWAY_SERVICE_ID`

### ✅ Must be Set as Secrets
- `JWT_SECRET_KEY`
- `MAILJET_API_KEY`
- `MAILJET_API_SECRET`
- `FROM_EMAIL`
- `FROM_NAME`
- `FRONTEND_URL`
- `ALLOWED_ORIGINS`
- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

### ✅ Pre-configured in railway.toml
- `ENVIRONMENT=production`
- `DEBUG=false`
- `DB_POOL_SIZE=20`
- `DB_MAX_OVERFLOW=30`

### ❌ Must NOT be Set
- `DEFAULT_USER_PASSWORD`

## 🧪 Testing Locally

To test the production configuration locally:

```bash
# Use the production environment file
cp .env.production .env.production.test

# Edit .env.production.test with your local values
# Then run:
ENVIRONMENT=production python scripts/start_production.py
```

## 📞 Support

If you continue having issues:

1. Check the Railway deployment logs for the diagnostic output
2. Verify all secrets are set correctly
3. Ensure PostgreSQL is properly attached
4. Confirm `DEFAULT_USER_PASSWORD` is not configured

The diagnostic script will show you exactly what's configured and what's missing.
