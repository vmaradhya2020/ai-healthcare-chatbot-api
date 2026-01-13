# Production Deployment Guide

This guide covers deploying the Healthcare Chatbot API to production environments.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Local Setup with MySQL](#local-setup-with-mysql)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Post-Deployment](#post-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- Python 3.11+
- MySQL 8.0+ (or PostgreSQL 14+)
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

### Recommended for Production
- Docker & Docker Compose
- Nginx or similar reverse proxy
- SSL/TLS certificates
- Monitoring solution (Sentry, DataDog, etc.)

---

## Pre-Deployment Checklist

### 1. Security Configuration

- [ ] Generate strong `SECRET_KEY`
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] Set strong database password
- [ ] Configure CORS with actual frontend URL (no localhost)
- [ ] Enable HTTPS/TLS
- [ ] Review and set rate limits
- [ ] Configure firewall rules
- [ ] Disable DEBUG mode (`ENVIRONMENT=production`)

### 2. Database Setup

- [ ] MySQL/PostgreSQL installed and running
- [ ] Database created with UTF8MB4 encoding
- [ ] Database user created with appropriate permissions
- [ ] Connection tested successfully
- [ ] Backup strategy in place

### 3. Environment Variables

Create `.env` file with production values:

```env
# CRITICAL: Change all default values!
SECRET_KEY=<your-secure-random-key>
ENVIRONMENT=production

# Database
DATABASE_URL=mysql+pymysql://user:password@host:3306/healthcaresense
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# API
CORS_ORIGINS=https://your domain.com,https://app.yourdomain.com

# OpenAI (if using)
OPENAI_API_KEY=sk-your-key-here

# Monitoring (optional but recommended)
SENTRY_DSN=https://your-sentry-dsn
```

### 4. Testing

- [ ] Run all tests: `pytest`
- [ ] Test database migrations: `alembic upgrade head`
- [ ] Test API endpoints
- [ ] Load testing completed
- [ ] Security scan completed

---

## Local Setup with MySQL

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup MySQL

```bash
# Run MySQL setup script
mysql -u root -p < scripts/setup_mysql.sql

# Or manually:
mysql -u root -p
```

```sql
CREATE DATABASE healthcaresense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'healthcareapp'@'localhost' IDENTIFIED BY 'YourStrongPassword!';
GRANT ALL PRIVILEGES ON healthcaresense.* TO 'healthcareapp'@'localhost';
FLUSH PRIVILEGES;
```

### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your values
# Make sure to set DATABASE_URL correctly!
```

### Step 4: Run Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Seed database (optional)
python seed_data.py
```

### Step 5: Start Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Production mode with Gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8001 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -
```

---

## Docker Deployment

### Option 1: Using Docker Compose (Recommended for Development/Staging)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

This will start:
- MySQL database
- API service
- Redis (for caching)

### Option 2: Docker Only (Production)

```bash
# Build image
docker build -t healthcaresense-api:latest .

# Run container
docker run -d \
    --name healthcaresense-api \
    -p 8001:8001 \
    --env-file .env \
    -e DATABASE_URL="mysql+pymysql://user:pass@host:3306/db" \
    healthcaresense-api:latest
```

### Running Migrations in Docker

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Seed database
docker-compose exec api python seed_data.py
```

---

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS (Elastic Container Service)

1. **Push Docker image to ECR**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker tag healthcaresense-api:latest YOUR_ECR_URL/healthcaresense-api:latest
docker push YOUR_ECR_URL/healthcaresense-api:latest
```

2. **Create RDS MySQL instance**
   - Engine: MySQL 8.0
   - Instance type: db.t3.medium (minimum)
   - Storage: 20GB with autoscaling
   - Enable automated backups
   - Set up VPC security groups

3. **Create ECS Task Definition**
```json
{
  "family": "healthcaresense-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "YOUR_ECR_URL/healthcaresense-api:latest",
      "portMappings": [{"containerPort": 8001}],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

4. **Configure Application Load Balancer**
   - Health check: `/health`
   - Readiness check: `/health/ready`

#### Using AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker healthcaresense-api

# Create environment
eb create healthcaresense-prod \
    --database.engine mysql \
    --database.username healthcareapp \
    --envvars SECRET_KEY=xxx,ENVIRONMENT=production

# Deploy
eb deploy
```

### Google Cloud Platform

#### Using Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/healthcaresense-api

# Deploy
gcloud run deploy healthcaresense-api \
    --image gcr.io/PROJECT_ID/healthcaresense-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production \
    --set-secrets=SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest
```

### Azure

#### Using Azure Container Instances

```bash
# Create resource group
az group create --name healthcaresense-rg --location eastus

# Create MySQL server
az mysql server create \
    --resource-group healthcaresense-rg \
    --name healthcaresense-mysql \
    --admin-user healthcareapp \
    --admin-password StrongPassword! \
    --sku-name GP_Gen5_2

# Deploy container
az container create \
    --resource-group healthcaresense-rg \
    --name healthcaresense-api \
    --image YOUR_REGISTRY/healthcaresense-api:latest \
    --ports 8001 \
    --environment-variables ENVIRONMENT=production \
    --secure-environment-variables SECRET_KEY=xxx DATABASE_URL=xxx
```

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Check health
curl https://your-api-domain.com/health

# Check readiness
curl https://your-api-domain.com/health/ready

# Check database connection
curl https://your-api-domain.com/health/ready
```

### 2. Run Database Migrations

```bash
# SSH into server or use container exec
alembic upgrade head
```

### 3. Seed Initial Data (if needed)

```bash
python seed_data.py
```

### 4. Test Critical Endpoints

```bash
# Register user
curl -X POST https://your-api-domain.com/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"Password123!","client_code":"CLIENT001"}'

# Login
curl -X POST https://your-api-domain.com/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"Password123!"}'

# Test chat (use token from login)
curl -X POST https://your-api-domain.com/chat \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message":"What is my order status?"}'
```

### 5. Configure Monitoring

**Sentry (Error Tracking)**
```env
SENTRY_DSN=https://your-sentry-dsn
```

**Health Check Monitoring**
Set up external monitoring (UptimeRobot, Pingdom, etc.) to check `/health` endpoint every 5 minutes.

---

## Monitoring & Maintenance

### Application Logs

```bash
# Docker
docker-compose logs -f api

# Direct logs
tail -f logs/app.log

# Filter for errors
docker-compose logs api | grep ERROR
```

### Database Monitoring

```sql
-- Check connections
SHOW PROCESSLIST;

-- Check slow queries
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;

-- Database size
SELECT
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'healthcaresense';
```

### Performance Metrics

Monitor these metrics:
- Response time (target: < 2 seconds)
- Error rate (target: < 1%)
- Database connection pool usage
- Memory usage
- CPU usage
- Request rate

### Backup Strategy

```bash
# Daily database backup
mysqldump -u healthcareapp -p healthcaresense > backup_$(date +%Y%m%d).sql

# Automated backup script
cat > /etc/cron.daily/mysql-backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u healthcareapp -pYOUR_PASSWORD healthcaresense | gzip > $BACKUP_DIR/healthcaresense_$DATE.sql.gz
# Keep only last 7 days
find $BACKUP_DIR -name "healthcaresense_*.sql.gz" -mtime +7 -delete
EOF
chmod +x /etc/cron.daily/mysql-backup.sh
```

### Security Updates

```bash
# Update dependencies
pip list --outdated
pip install --upgrade -r requirements.txt

# Security audit
pip install safety
safety check

# Rebuild Docker image with updates
docker-compose build --no-cache
docker-compose up -d
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
python -c "from app.database import check_database_connection; print(check_database_connection())"

# Check MySQL status
systemctl status mysql

# Check connection from app server
mysql -h DB_HOST -u healthcareapp -p healthcaresense
```

### High Memory Usage

```bash
# Check container stats
docker stats healthcaresense-api

# Reduce workers in Gunicorn
gunicorn app.main:app --workers 2  # Instead of 4

# Adjust pool size in .env
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Slow Responses

1. Check database query performance
2. Review logs for slow endpoints
3. Enable query logging in database
4. Consider adding Redis for caching
5. Optimize database indexes

### Rate Limit Issues

```bash
# Adjust in .env
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=2000
```

---

## Rollback Procedure

### Application Rollback

```bash
# Docker
docker-compose pull  # Get previous version
docker-compose up -d

# Or specific version
docker run -d YOUR_ECR_URL/healthcaresense-api:PREVIOUS_TAG
```

### Database Rollback

```bash
# Downgrade one migration
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade REVISION_ID

# Restore from backup
mysql -u healthcareapp -p healthcaresense < backup_YYYYMMDD.sql
```

---

## Support & Escalation

### Before Contacting Support

1. Check application logs
2. Check database logs
3. Verify environment variables
4. Test database connection
5. Check external service status (OpenAI API, etc.)

### Log Collection

```bash
# Collect logs for support
docker-compose logs api > api_logs.txt
docker-compose logs mysql > mysql_logs.txt

# System information
docker info > system_info.txt
docker-compose ps > services_status.txt
```

---

## Compliance Notes

### HIPAA Compliance Checklist

- [ ] All data encrypted at rest
- [ ] All data encrypted in transit (HTTPS)
- [ ] Access logs enabled and retained
- [ ] Audit trails for PHI access
- [ ] Regular security assessments
- [ ] Backup and disaster recovery plan
- [ ] Business Associate Agreements in place

### Data Retention

As configured in `.env`:
- Chat logs: 7 years (2555 days)
- Audit logs: 7 years (2555 days)

Configure automatic data cleanup:
```sql
-- Delete old chat logs
DELETE FROM chat_log WHERE timestamp < DATE_SUB(NOW(), INTERVAL 2555 DAY);
```

---

For additional help, refer to:
- [MySQL Setup Guide](docs/MYSQL_SETUP.md)
- [API Documentation](http://localhost:8001/docs)
- [Alembic Migration Guide](alembic/README.md)
