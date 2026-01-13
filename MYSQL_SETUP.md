# MySQL Setup Guide for Healthcare Chatbot API

This guide will help you set up MySQL for the Healthcare Chatbot API.

## Prerequisites

- MySQL 8.0 or higher installed locally
- MySQL command-line client or MySQL Workbench

## Step-by-Step Setup

### Step 1: Access MySQL as Root

Open your terminal/command prompt and log in to MySQL:

```bash
mysql -u root -p
```

Enter your MySQL root password when prompted.

### Step 2: Run the Setup Script

From the MySQL prompt, run the setup script:

```sql
source C:\capstone_ic_ik\ai-healthcare-chatbot-api-main\scripts\setup_mysql.sql
```

Or on Windows, you can run:

```bash
mysql -u root -p < C:\capstone_ic_ik\ai-healthcare-chatbot-api-main\scripts\setup_mysql.sql
```

This script will:
- Create the `healthcaresense` database with UTF8MB4 encoding
- Create a user `healthcareapp` with a default password
- Grant necessary permissions

### Step 3: Update the Password (IMPORTANT!)

**Security Warning:** The default password in the script is `Change_This_Password_123!`

You MUST change this before using in production:

```sql
ALTER USER 'healthcareapp'@'localhost' IDENTIFIED BY 'YourSecurePassword!';
FLUSH PRIVILEGES;
```

### Step 4: Create/Update .env File

Create a `.env` file in the project root (if it doesn't exist):

```bash
cp .env.example .env
```

Update the DATABASE_URL in `.env`:

```env
# For local development
DATABASE_URL=mysql+pymysql://healthcareapp:YourSecurePassword!@localhost:3306/healthcaresense

# IMPORTANT: Replace 'YourSecurePassword!' with the password you set in Step 3
```

### Step 5: Install Python Dependencies

Make sure you have all required packages:

```bash
pip install -r requirements.txt
```

### Step 6: Initialize Database with Alembic

Run the initial migration to create all tables:

```bash
# Create the initial migration (only needed once)
alembic revision --autogenerate -m "Initial schema"

# Apply the migration
alembic upgrade head
```

### Step 7: Seed the Database (Optional)

Populate the database with sample data:

```bash
python seed_data.py
```

### Step 8: Verify the Setup

Test the database connection:

```bash
python -c "from app.database import check_database_connection; print('Connection OK' if check_database_connection() else 'Connection Failed')"
```

Or start the application and check the health endpoint:

```bash
uvicorn app.main:app --reload
```

Then visit: http://localhost:8001/db-health

## Troubleshooting

### Error: "Access denied for user"

**Problem:** Wrong password or user doesn't exist.

**Solution:**
1. Check your .env file has the correct password
2. Verify the user exists: `SELECT User, Host FROM mysql.user WHERE User = 'healthcareapp';`
3. Reset the password if needed

### Error: "Unknown database 'healthcaresense'"

**Problem:** Database was not created.

**Solution:**
```sql
CREATE DATABASE healthcaresense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Error: "Can't connect to MySQL server"

**Problem:** MySQL service is not running.

**Solution:**
- **Windows:** Check Services (services.msc) and start "MySQL80" service
- **Linux:** `sudo systemctl start mysql`
- **macOS:** `brew services start mysql`

### Error: "Connection timeout"

**Problem:** MySQL is not listening on localhost:3306 or firewall is blocking.

**Solution:**
1. Check MySQL is running: `mysql -u root -p`
2. Verify port: `SHOW VARIABLES LIKE 'port';`
3. Check firewall settings

## Production Deployment Considerations

### 1. Use Strong Passwords

Generate a secure password:

```python
import secrets
password = secrets.token_urlsafe(32)
print(password)
```

### 2. Enable SSL/TLS Connections

For production, configure SSL in MySQL and update DATABASE_URL:

```env
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/client-cert.pem&ssl_key=/path/to/client-key.pem
```

### 3. Configure Connection Pooling

Already configured in `app/database.py`:
- Pool size: 5
- Max overflow: 10
- Pool recycle: 3600 seconds

Adjust in `.env` if needed:
```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### 4. Regular Backups

Set up automated backups:

```bash
# Daily backup script
mysqldump -u healthcareapp -p healthcaresense > backup_$(date +%Y%m%d).sql

# Or use MySQL Enterprise Backup
```

### 5. Monitoring

Enable slow query log:

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';
```

### 6. Performance Tuning

Key MySQL settings for production (in my.cnf/my.ini):

```ini
[mysqld]
# InnoDB settings
innodb_buffer_pool_size = 2G
innodb_log_file_size = 512M
innodb_flush_log_at_trx_commit = 2
innodb_file_per_table = 1

# Connection settings
max_connections = 200
wait_timeout = 600

# Character set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

## Useful MySQL Commands

### View all databases
```sql
SHOW DATABASES;
```

### View all tables in healthcaresense
```sql
USE healthcaresense;
SHOW TABLES;
```

### View table structure
```sql
DESCRIBE users;
```

### Check database size
```sql
SELECT
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'healthcaresense'
GROUP BY table_schema;
```

### View active connections
```sql
SHOW PROCESSLIST;
```

### Check MySQL version
```sql
SELECT VERSION();
```

## Migration from SQLite (If Needed)

If you have existing data in SQLite and want to migrate:

### Option 1: Manual Export/Import

```bash
# Export data from SQLite
sqlite3 healthcare.db .dump > data.sql

# Edit data.sql to make it MySQL compatible
# Then import:
mysql -u healthcareapp -p healthcaresense < data.sql
```

### Option 2: Use a migration tool

```bash
pip install sqlite3-to-mysql
sqlite3mysql -f healthcare.db -d healthcaresense -u healthcareapp -p
```

## Support

For issues specific to this project, check:
- Application logs
- MySQL error log: `/var/log/mysql/error.log` (Linux) or check MySQL Workbench (Windows)
- Connection settings in `.env`

For MySQL help:
- Official MySQL Documentation: https://dev.mysql.com/doc/
- MySQL Community: https://forums.mysql.com/
