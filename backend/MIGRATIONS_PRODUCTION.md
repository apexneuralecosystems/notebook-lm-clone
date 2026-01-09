# Database Migrations in Production

## Overview

The backend Docker container now **automatically runs database migrations** on startup before starting the FastAPI server.

## How It Works

1. **Container starts** → Entrypoint script runs
2. **Wait for database** → Script waits for PostgreSQL to be ready
3. **Run migrations** → `alembic upgrade head` runs automatically
4. **Start server** → FastAPI server starts after migrations complete

## Entrypoint Script

The `docker-entrypoint.sh` script:
- Waits for database connection (retries every 2 seconds)
- Runs `alembic upgrade head` to apply all pending migrations
- Starts the FastAPI server with uvicorn

## In Dokploy

### Automatic Migrations

Migrations run automatically when:
- Backend container starts
- Backend container restarts
- Backend service is redeployed

**No manual intervention needed!**

### Environment Variables

Ensure these are set in **Dokploy Backend Environments**:

```env
# Database connection (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/notebooklm
# OR use individual components:
DATABASE_HOST=your-postgres-host
DATABASE_PORT=5432
DATABASE_NAME=notebooklm
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password

# Backend server
BACKEND_PORT=8102
BACKEND_HOST=0.0.0.0
```

### Migration Logs

Check backend logs in Dokploy to see migration output:

```
==========================================
Starting NotebookLM Backend
==========================================
Waiting for database to be ready...
Database is ready!
==========================================
Running database migrations...
==========================================
INFO  [alembic.runtime.migration] Context impl AsyncImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade -> abc123, create_users_table
==========================================
Migrations completed
==========================================
Starting FastAPI server...
INFO:     Uvicorn running on http://0.0.0.0:8102
```

## Manual Migration (If Needed)

If you need to run migrations manually:

### Option 1: Via Dokploy Shell/Execute

If Dokploy has a shell/execute feature:
```bash
uv run alembic upgrade head
```

### Option 2: Via Docker Exec

If you have direct Docker access:
```bash
docker exec <backend-container> uv run alembic upgrade head
```

### Option 3: Check Current Migration

To see current migration status:
```bash
uv run alembic current
```

## Troubleshooting

### Migration Fails on Startup

**Symptom:** Container keeps restarting, migrations fail

**Common Causes:**
1. **Database not accessible**
   - Check `DATABASE_URL` is correct
   - Verify database is running
   - Check network connectivity

2. **Database credentials wrong**
   - Verify `DATABASE_PASSWORD` is correct
   - Check `DATABASE_USER` has permissions

3. **Migration conflicts**
   - Check migration history: `alembic history`
   - May need to resolve conflicts manually

**Fix:**
- Check backend logs for specific error
- Verify database connection
- Test database connection manually

### Migrations Already Applied

**Symptom:** Logs show "No migrations to apply" or similar

**Status:** This is **normal** - migrations are idempotent
- If migrations are already applied, Alembic skips them
- Container continues and starts server normally

### Database Not Ready

**Symptom:** "Database is unavailable - sleeping" messages

**Status:** Entrypoint script waits for database
- Retries every 2 seconds
- Continues once database is ready
- This is expected if database starts after backend

**If it keeps waiting:**
- Check database is running
- Verify `DATABASE_URL` is correct
- Check network connectivity

## Migration Best Practices

1. **Always test migrations locally** before deploying
2. **Backup database** before running migrations in production
3. **Review migration files** before applying
4. **Monitor logs** during first deployment after adding migrations

## Disabling Auto-Migrations

If you need to disable automatic migrations (not recommended):

1. Modify `docker-entrypoint.sh` to skip migration step
2. Or use original CMD instead of ENTRYPOINT

**Note:** You'll need to run migrations manually if disabled.

## Migration Commands Reference

```bash
# Upgrade to latest
uv run alembic upgrade head

# Upgrade to specific revision
uv run alembic upgrade <revision>

# Check current migration
uv run alembic current

# View migration history
uv run alembic history

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Downgrade one step
uv run alembic downgrade -1
```

