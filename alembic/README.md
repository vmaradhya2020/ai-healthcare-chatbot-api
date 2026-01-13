# Database Migrations with Alembic

This directory contains database migration scripts for the Healthcare Chatbot API.

## Quick Start

### Create Initial Migration
```bash
# Generate initial migration from current models
alembic revision --autogenerate -m "Initial migration"
```

### Apply Migrations
```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version at a time
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>
```

### Check Status
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show SQL that would be executed (don't actually run it)
alembic upgrade head --sql
```

## Creating Migrations

### Auto-generate from Model Changes
```bash
alembic revision --autogenerate -m "Add user roles table"
```

### Create Empty Migration (for data migrations)
```bash
alembic revision -m "Migrate user data"
```

## Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Test migrations on a copy of production data** before deploying
3. **Create a database backup** before running migrations in production
4. **Keep migrations small** - one logical change per migration
5. **Never modify existing migrations** that have been applied to production
6. **Always provide downgrade paths** for rollback capability

## Migration Workflow

### Development
```bash
# 1. Make changes to models in app/models.py
# 2. Generate migration
alembic revision --autogenerate -m "Description of changes"

# 3. Review the generated migration file in alembic/versions/
# 4. Apply the migration
alembic upgrade head

# 5. Test thoroughly
# 6. Commit both model changes AND migration files to git
```

### Production Deployment
```bash
# 1. Backup database
mysqldump -u user -p healthcaresense > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply migrations
alembic upgrade head

# 3. If something goes wrong, rollback
alembic downgrade -1

# 4. Restore from backup if needed
mysql -u user -p healthcaresense < backup_YYYYMMDD_HHMMSS.sql
```

## Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
alembic current

# Check what migrations exist
alembic history

# Stamp database to specific version (use carefully!)
alembic stamp head
```

### "Can't locate revision identified by"
This usually means the alembic_version table is out of sync.
```bash
# Check alembic_version table
mysql -u user -p healthcaresense -e "SELECT * FROM alembic_version;"

# Stamp to correct version
alembic stamp <correct_revision_id>
```

### Autogenerate not detecting changes
Make sure:
1. Models are imported in `alembic/env.py`
2. Models inherit from `Base`
3. .env file has correct DATABASE_URL
4. Database connection is working

## Common Operations

### Add a new column
```bash
alembic revision --autogenerate -m "Add email_verified column to users"
```

### Rename a table
```python
# In migration file
def upgrade():
    op.rename_table('old_name', 'new_name')

def downgrade():
    op.rename_table('new_name', 'old_name')
```

### Add an index
```python
def upgrade():
    op.create_index('idx_user_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_user_email', 'users')
```

### Data migration example
```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade():
    # Get a connection
    conn = op.get_bind()

    # Define table structure (just what we need)
    users = table('users',
        column('id', sa.Integer),
        column('old_status', sa.String),
        column('new_status', sa.String)
    )

    # Update data
    conn.execute(
        users.update().
        where(users.c.old_status == 'active').
        values(new_status='verified')
    )
```

## MySQL Specific Notes

- Use `mysql+pymysql://` in DATABASE_URL
- Ensure utf8mb4 charset for emoji support
- Be careful with VARCHAR lengths (max 255 for indexed columns)
- InnoDB is the default engine (supports transactions)

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy Column Types](https://docs.sqlalchemy.org/en/20/core/type_basics.html)
