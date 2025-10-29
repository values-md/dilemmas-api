# Deployment Guide: Fly.io + Neon Postgres

Complete guide to deploying the VALUES.md Dilemmas API to production.

---

## Prerequisites

1. **Fly.io account** - Sign up at https://fly.io
2. **Neon account** - Sign up at https://neon.tech (free tier)
3. **Fly CLI** installed:
   ```bash
   brew install flyctl
   # or on Linux/WSL:
   curl -L https://fly.io/install.sh | sh
   ```

---

## Step 1: Set Up Neon Postgres Database

### Create Database

1. Go to https://neon.tech/console
2. Create a new project
3. Name it: `values-md-dilemmas`
4. Select region (choose closest to your Fly.io primary_region)
5. Copy the connection string from the dashboard

The connection string will look like:
```
postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### Test Connection Locally

```bash
# Set DATABASE_URL temporarily
export DATABASE_URL="postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require"

# Run migrations
uv run alembic upgrade head

# Test that it works
uv run python -c "from dilemmas.db.database import get_database; import asyncio; db = get_database(); asyncio.run(db.close()); print('✓ Connection successful')"
```

---

## Step 2: Deploy to Fly.io

### Login to Fly

```bash
flyctl auth login
```

### Launch App (First Time)

```bash
# From project root
flyctl launch

# Answer prompts:
# - App name: values-md-dilemmas (or choose your own)
# - Region: sjc (San Jose) or your preferred region
# - Add Postgres database? NO (we're using Neon)
# - Deploy now? NO (we need to set secrets first)
```

This creates/updates `fly.toml` with your app name and region.

### Set Environment Secrets

```bash
# Database connection
flyctl secrets set DATABASE_URL="postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require"

# OpenRouter API key (for dilemma generation)
flyctl secrets set OPENROUTER_API_KEY="sk-or-v1-..."

# API key for protected endpoints (generate a random secure key)
flyctl secrets set API_KEY="$(openssl rand -hex 32)"

# Save the API_KEY somewhere safe - you'll need it to access protected endpoints!
```

### Deploy

```bash
flyctl deploy
```

This will:
1. Build the Docker image
2. Push it to Fly.io
3. Start the container
4. Run migrations automatically via entrypoint.sh
5. Start the FastAPI server

### Monitor Deployment

```bash
# View logs
flyctl logs

# Check status
flyctl status

# Open in browser
flyctl open
```

---

## Step 3: Verify Deployment

### Check Health

```bash
# Basic health check
curl https://values-md-dilemmas.fly.dev/research

# Check API (replace with your actual API key)
curl -H "X-API-Key: your-api-key-here" \
     https://values-md-dilemmas.fly.dev/api/stats
```

### Test Dilemma Generation

```bash
curl -X POST https://values-md-dilemmas.fly.dev/api/generate \
     -H "X-API-Key: your-api-key-here" \
     -H "Content-Type: application/json" \
     -d '{
       "difficulty": 7,
       "prompt_version": "v8_concise"
     }'
```

---

## Step 4: Initial Data Migration (Optional)

If you want to migrate existing data from local SQLite to production Neon:

### Export from SQLite

```bash
# Export dilemmas
uv run python scripts/export_all_dilemmas.py > dilemmas_export.json

# Or use database dump
sqlite3 data/dilemmas.db .dump > dump.sql
```

### Import to Neon

```bash
# Option 1: Use Python script to bulk insert
export DATABASE_URL="postgresql://..."
uv run python scripts/import_dilemmas.py dilemmas_export.json

# Option 2: Convert SQLite dump to Postgres and import
# (requires manual conversion of SQLite -> Postgres syntax)
```

---

## Ongoing Operations

### View Logs

```bash
# Tail logs
flyctl logs

# Filter by level
flyctl logs --level error
```

### Update Deployment

```bash
# After making code changes
flyctl deploy

# Migrations will run automatically on deploy!
```

### Database Migrations

Migrations run automatically on every deploy via `entrypoint.sh`.

To run migrations manually:

```bash
# SSH into the running container
flyctl ssh console

# Inside container:
uv run alembic upgrade head
exit
```

### Scale Resources

```bash
# Scale to 2 machines
flyctl scale count 2

# Increase memory
flyctl scale memory 1024  # 1GB

# View current scaling
flyctl scale show
```

### Restart App

```bash
flyctl apps restart values-md-dilemmas
```

---

## Troubleshooting

### Migrations Fail on Deploy

```bash
# Check logs for migration errors
flyctl logs --search "alembic"

# SSH in and run migrations manually
flyctl ssh console
uv run alembic upgrade head
```

### Cannot Connect to Database

```bash
# Verify DATABASE_URL is set
flyctl secrets list

# Test connection from inside container
flyctl ssh console
echo $DATABASE_URL
uv run python -c "from dilemmas.db.database import get_database; import asyncio; db = get_database(); asyncio.run(db.close()); print('OK')"
```

### API Key Not Working

```bash
# Verify API_KEY is set
flyctl secrets list

# Reset it
flyctl secrets set API_KEY="new-key-here"
```

### App Won't Start

```bash
# Check deployment status
flyctl status

# View detailed logs
flyctl logs

# Check if health checks are passing
flyctl checks list
```

---

## Cost Estimate

**Neon Postgres (Free Tier)**
- ✅ 0.5GB storage
- ✅ 1 branch
- ✅ No credit card required

**Fly.io (Hobby Plan)**
- Shared CPU: $0/month for first machine
- 256MB RAM: ~$1.94/month
- Additional machines: ~$1.94/month each

**Total**: ~$0-2/month for low-traffic deployment

---

## Production Checklist

Before deploying to production:

- [ ] Database URL is set and tested
- [ ] API_KEY is set and saved securely
- [ ] OPENROUTER_API_KEY is set (if using generation)
- [ ] fly.toml has correct app name and region
- [ ] Migrations run successfully
- [ ] Health checks pass
- [ ] Research pages load correctly
- [ ] Protected endpoints require API key
- [ ] Monitor logs for first 24 hours

---

## API Endpoints Reference

### Public (No Auth)

- `GET /` - Dilemmas browser
- `GET /research` - Research experiments index
- `GET /research/{slug}` - Experiment findings
- `GET /dilemma/{id}` - Single dilemma view

### Protected (Requires X-API-Key header)

- `POST /api/generate` - Generate new dilemma
- `GET /api/dilemmas` - List/search dilemmas
- `GET /api/dilemma/{id}` - Get dilemma JSON
- `GET /api/stats` - Database statistics

---

## Monitoring & Maintenance

### Weekly Tasks

- Check logs for errors: `flyctl logs --level error`
- Review disk usage on Neon dashboard
- Check app health: `flyctl status`

### Monthly Tasks

- Review Neon storage usage (0.5GB limit on free tier)
- Check Fly.io billing dashboard
- Update dependencies: `uv lock --upgrade`

### Alerts Setup

Set up Fly.io health check alerts:

```bash
flyctl checks list
```

Configure email notifications in Fly.io dashboard.

---

## Rollback

If deployment fails:

```bash
# View releases
flyctl releases

# Rollback to previous version
flyctl releases rollback <release-id>
```

---

## Next Steps

1. Set up custom domain (optional)
   ```bash
   flyctl certs add yourdomain.com
   ```

2. Enable HTTPS redirect (already configured in fly.toml)

3. Set up monitoring (https://fly.io/docs/reference/metrics/)

4. Configure autoscaling (https://fly.io/docs/reference/scaling/)

---

## Support

- Fly.io Docs: https://fly.io/docs/
- Neon Docs: https://neon.tech/docs/
- Project Issues: https://github.com/your-repo/issues
