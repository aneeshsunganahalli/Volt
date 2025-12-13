# Heroku Deployment Guide for Kronyx

This guide explains how to deploy the Kronyx server application to Heroku with Redis support.

## Prerequisites

1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Have a Heroku account
3. Git repository initialized

## Setup Steps

### 1. Login to Heroku
```bash
heroku login
```

### 2. Create a New Heroku App
```bash
cd server
heroku create your-app-name
```

### 3. Add Redis Add-on
Heroku provides Redis through add-ons. The basic plan is free for development:

```bash
# For free tier (suitable for development)
heroku addons:create heroku-redis:mini

# Or for production with more capacity
heroku addons:create heroku-redis:premium-0
```

This automatically sets the `REDIS_URL` environment variable.

### 4. Add PostgreSQL Database (Recommended for Production)
SQLite doesn't work well on Heroku's ephemeral filesystem. Use PostgreSQL instead:

```bash
heroku addons:create heroku-postgresql:essential-0
```

This sets the `DATABASE_URL` environment variable automatically.

### 5. Set Environment Variables
Set all required environment variables:

```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set ALGORITHM="HS256"
heroku config:set ACCESS_TOKEN_EXPIRE_MINUTES=30
heroku config:set APP_NAME="Kronyx"

# Redis configuration (if not using REDIS_URL from add-on)
# Note: If you added heroku-redis, REDIS_URL is set automatically
# You may need to parse it or set individual variables
heroku config:set REDIS_DB=0
heroku config:set REDIS_QUEUE_NAME="transaction_queue"

# Email polling interval (in seconds)
heroku config:set IMAP_POLL_INTERVAL=300

# Gemini API Key
heroku config:set GEMINI_API_KEY="your-gemini-api-key"

# Twilio Configuration (if using WhatsApp integration)
heroku config:set TWILIO_ACCOUNT_SID="your-twilio-sid"
heroku config:set TWILIO_AUTH_TOKEN="your-twilio-token"
heroku config:set TWILIO_WHATSAPP_FROM="whatsapp:+14155238886"
heroku config:set TWILIO_CONTENT_SID="your-content-sid"

# Default user ID for worker
heroku config:set DEFAULT_USER_ID=1
```

### 6. Configure Redis Connection
If using Heroku Redis, the connection URL is provided as `REDIS_URL`. You may need to update your code to parse this URL. Add this to your configuration:

```python
import os
from urllib.parse import urlparse

# Parse REDIS_URL if available (Heroku format)
redis_url = os.getenv('REDIS_URL')
if redis_url:
    parsed = urlparse(redis_url)
    REDIS_HOST = parsed.hostname
    REDIS_PORT = parsed.port
    REDIS_PASSWORD = parsed.password
else:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
```

### 7. Deploy Using Git

**Option A: Using Procfile (Standard Deployment)**
```bash
git add .
git commit -m "Add Heroku configuration"
git push heroku main
```

**Option B: Using Docker (Container Registry)**
If you prefer Docker deployment:
```bash
# Login to Heroku Container Registry
heroku container:login

# Set stack to container
heroku stack:set container

# Push and release
heroku container:push web worker poller
heroku container:release web worker poller
```

### 8. Scale Dynos
Configure how many instances of each process type to run:

```bash
# Scale web dynos (API server)
heroku ps:scale web=1

# Scale worker dynos (transaction processor)
heroku ps:scale worker=1

# Scale poller dynos (email polling)
heroku ps:scale poller=1
```

**Note:** Free tier only allows 1 web dyno. Worker and poller dynos require paid plans.

### 9. Run Database Migrations
```bash
heroku run alembic upgrade head
```

Or if you added a release phase in Procfile, migrations run automatically on deploy.

### 10. View Logs
```bash
# View all logs
heroku logs --tail

# View specific process logs
heroku logs --tail --dyno=web
heroku logs --tail --dyno=worker
heroku logs --tail --dyno=poller
```

## Process Types Explained

- **web**: The FastAPI application that handles HTTP requests
- **worker**: Background worker that processes transactions from Redis queue
- **poller**: Email polling service that checks for new transaction emails
- **release**: Runs database migrations before deployment

## Redis Management

### Check Redis Status
```bash
heroku redis:info
```

### View Redis Credentials
```bash
heroku config:get REDIS_URL
```

### Access Redis CLI
```bash
heroku redis:cli
```

### Monitor Redis
```bash
heroku redis:monitor
```

## PostgreSQL Management

### Access Database
```bash
heroku pg:psql
```

### View Database Info
```bash
heroku pg:info
```

### Backup Database
```bash
heroku pg:backups:capture
heroku pg:backups:download
```

## Troubleshooting

### Check App Status
```bash
heroku ps
```

### Restart Dynos
```bash
heroku restart
```

### Check Config Variables
```bash
heroku config
```

### Debug Build Issues
```bash
heroku builds:info
```

### Scale Issues
If workers/pollers aren't running:
1. Check if you're on free tier (only allows 1 web dyno)
2. Upgrade to paid plan to run background workers
3. Scale dynos: `heroku ps:scale worker=1 poller=1`

## Cost Considerations

### Free Tier Limitations:
- Only 1 web dyno
- No worker/poller dynos
- 550-1000 free dyno hours/month
- Redis mini plan: 25MB storage
- PostgreSQL essential-0: 1GB storage

### For Production:
- Upgrade to Hobby or Professional dynos
- Use Premium Redis plans for better performance
- Consider Standard PostgreSQL plans

## Custom Domain (Optional)
```bash
heroku domains:add www.yourdomain.com
```

## CI/CD Integration
Connect to GitHub for automatic deployments:
```bash
heroku git:remote -a your-app-name
```

Then enable GitHub integration in Heroku Dashboard:
1. Go to Deploy tab
2. Connect to GitHub
3. Enable Automatic Deploys

## Health Checks
Your app should respond to health checks at the root endpoint. Heroku automatically monitors this.

## Updating Environment Variables
```bash
heroku config:set VARIABLE_NAME=new_value
```

Changes take effect immediately after dyno restart.

## Useful Commands

```bash
# Open app in browser
heroku open

# Run one-off commands
heroku run python update_user_phone.py

# View releases
heroku releases

# Rollback to previous release
heroku rollback

# Check app size
heroku apps:info
```

## Support

For issues specific to Heroku:
- Documentation: https://devcenter.heroku.com/
- Status: https://status.heroku.com/
