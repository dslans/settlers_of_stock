# Settlers of Stock - Deployment Guide

This document provides comprehensive instructions for deploying and maintaining the Settlers of Stock application on Google Cloud Platform (GCP).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Application Deployment](#application-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Maintenance Operations](#maintenance-operations)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)

## Prerequisites

### Required Tools

- **Google Cloud SDK (gcloud)**: Latest version
- **Terraform**: Version 1.0 or higher
- **Docker**: For local testing and container builds
- **Node.js**: Version 18 or higher (for frontend builds)
- **Python**: Version 3.11 or higher
- **Git**: For source code management

### GCP Account Setup

1. Create a GCP project or use an existing one
2. Enable billing for the project
3. Install and authenticate gcloud CLI:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

### Required GCP APIs

The following APIs will be automatically enabled during deployment:
- App Engine Admin API
- Cloud Build API
- Cloud SQL Admin API
- Cloud Memorystore for Redis API
- Cloud Storage API
- Secret Manager API
- Cloud Monitoring API
- Cloud Logging API
- Vertex AI API
- BigQuery API
- Cloud Firestore API

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/settlers-of-stock.git
cd settlers-of-stock
```

### 2. Configure Project Settings

Edit the deployment script with your project details:

```bash
# Edit scripts/deploy.sh
PROJECT_ID="your-gcp-project-id"
GITHUB_OWNER="your-github-username"
GITHUB_REPO="settlers-of-stock"
```

### 3. Set Up Terraform Variables

Create `infrastructure/terraform/terraform.tfvars`:

```hcl
project_id = "your-gcp-project-id"
environment = "production"
region = "us-central1"
github_owner = "your-github-username"
github_repo = "settlers-of-stock"
admin_email = "admin@yourdomain.com"

# Database configuration
database_password = "your-secure-database-password"
db_tier = "db-f1-micro"  # Adjust based on needs

# Application secrets
app_secret_key = "your-jwt-secret-key"

# External API keys (optional)
alpha_vantage_api_key = "your-alpha-vantage-key"
news_api_key = "your-news-api-key"
reddit_client_id = "your-reddit-client-id"
reddit_client_secret = "your-reddit-client-secret"

# SMTP configuration (optional)
smtp_host = "smtp.gmail.com"
smtp_user = "your-email@gmail.com"
smtp_password = "your-app-password"

# Monitoring
app_domain = "your-app-domain.com"
slack_webhook_url = "your-slack-webhook-url"  # Optional
```

## Infrastructure Deployment

### Deploy with Terraform

The infrastructure includes:
- Cloud SQL PostgreSQL database
- Cloud Memorystore Redis cache
- Cloud Storage buckets
- BigQuery dataset
- Firestore database
- VPC network and security
- IAM service accounts
- Secret Manager secrets
- Monitoring and alerting

```bash
# Deploy infrastructure only
./scripts/deploy.sh --infrastructure-only

# Or deploy everything
./scripts/deploy.sh
```

### Manual Terraform Deployment

If you prefer to run Terraform manually:

```bash
cd infrastructure/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## Application Deployment

### Automated Deployment

The deployment script handles:
- Building the application
- Running tests
- Deploying to App Engine
- Setting up Cloud Build triggers

```bash
# Deploy application only (after infrastructure is ready)
./scripts/deploy.sh --application-only
```

### Manual Deployment Steps

1. **Prepare the backend:**
   ```bash
   cd backend
   # Install dependencies
   uv pip install -r requirements.txt
   
   # Run tests
   python -m pytest tests/ -v
   ```

2. **Prepare the frontend:**
   ```bash
   cd frontend
   npm ci
   npm run test:ci
   npm run build
   ```

3. **Deploy to App Engine:**
   ```bash
   cd backend
   gcloud app deploy app.yaml --project=YOUR_PROJECT_ID
   ```

4. **Deploy frontend to Cloud Storage:**
   ```bash
   gsutil -m rsync -r -d ./frontend/build/ gs://YOUR_PROJECT_ID-frontend/
   ```

## Environment Configuration

### Production Environment

The production environment uses:
- **App Engine**: Standard environment with Python 3.11
- **Cloud SQL**: PostgreSQL with automated backups
- **Cloud Memorystore**: Redis for caching
- **Secret Manager**: For sensitive configuration
- **Cloud Storage**: For static assets and file storage

### Environment Variables

Production environment variables are managed through:
1. **app.yaml**: Non-sensitive configuration
2. **Secret Manager**: Sensitive values (API keys, passwords)
3. **Environment-specific .env files**: `.env.production`

### Secret Management

Secrets are automatically loaded from Google Secret Manager in production:

```python
# Secrets are loaded automatically in production
# See backend/app/core/config.py for implementation
```

To update secrets:
```bash
./scripts/maintenance.sh secrets
```

## Monitoring and Alerting

### Built-in Monitoring

The application includes:
- **Health checks**: `/health` and `/status` endpoints
- **Custom metrics**: Performance and business metrics
- **Error tracking**: Automatic error logging and alerting
- **Uptime monitoring**: External health checks

### Monitoring Dashboard

Access the monitoring dashboard:
1. Go to Google Cloud Console
2. Navigate to Monitoring
3. Find "Settlers of Stock - Application Dashboard"

### Alert Policies

Configured alerts for:
- Application downtime
- High error rates
- High response latency
- Database connection issues
- Redis memory usage

### Log Analysis

View logs:
```bash
# Application logs
./scripts/maintenance.sh logs

# Error logs only
./scripts/maintenance.sh errors

# Or use gcloud directly
gcloud logging read "resource.type=gae_app" --limit=100
```

## Maintenance Operations

### Health Checks

```bash
# Check overall application health
./scripts/maintenance.sh health

# Check database status
./scripts/maintenance.sh database

# Check Redis status
./scripts/maintenance.sh redis
```

### Database Operations

```bash
# Create manual backup
./scripts/maintenance.sh backup

# List recent backups
./scripts/maintenance.sh backups

# Run database migrations
./scripts/maintenance.sh migrations
```

### Scaling

```bash
# Scale application instances
./scripts/maintenance.sh scale 2 20  # min=2, max=20
```

### Metrics and Performance

```bash
# View key metrics
./scripts/maintenance.sh metrics
```

### Secret Updates

```bash
# Update application secrets
./scripts/maintenance.sh secrets
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Symptoms**: Health checks fail, 502/503 errors

**Solutions**:
1. Check application logs:
   ```bash
   ./scripts/maintenance.sh logs 200
   ```
2. Verify database connectivity
3. Check secret manager access
4. Validate environment configuration

#### 2. Database Connection Issues

**Symptoms**: Database-related errors in logs

**Solutions**:
1. Check database status:
   ```bash
   ./scripts/maintenance.sh database
   ```
2. Verify VPC connectivity
3. Check database user permissions
4. Review connection string in secrets

#### 3. High Memory Usage

**Symptoms**: Application restarts, performance issues

**Solutions**:
1. Check Redis memory usage
2. Review application memory consumption
3. Scale up instance class if needed
4. Optimize caching strategies

#### 4. External API Failures

**Symptoms**: Analysis features not working

**Solutions**:
1. Check API key configuration
2. Verify rate limits
3. Review external service status
4. Check network connectivity

### Debug Commands

```bash
# Connect to database
gcloud sql connect INSTANCE_NAME --user=app_user

# View detailed application status
curl https://your-app-url.com/status

# Check Cloud Build history
gcloud builds list --limit=10

# View secret versions
gcloud secrets versions list SECRET_NAME
```

## Security Considerations

### Access Control

- **IAM**: Principle of least privilege
- **Service Accounts**: Dedicated accounts for different services
- **VPC**: Private networking for database and Redis
- **SSL/TLS**: Enforced for all connections

### Secret Management

- **Secret Manager**: All sensitive data stored securely
- **Rotation**: Regular rotation of secrets and passwords
- **Access Logging**: Audit trail for secret access

### Network Security

- **Private IPs**: Database and Redis use private networking
- **Firewall Rules**: Restrictive ingress/egress rules
- **SSL Certificates**: Managed certificates for HTTPS

### Data Protection

- **Encryption**: Data encrypted at rest and in transit
- **Backups**: Automated and encrypted backups
- **Access Logs**: Comprehensive audit logging

### Compliance

- **GDPR**: User data protection measures
- **SOC 2**: Security controls and monitoring
- **PCI DSS**: If handling payment data

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Backup created
- [ ] Monitoring configured
- [ ] Secrets updated
- [ ] Documentation updated

### Post-Deployment

- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Performance metrics normal
- [ ] User acceptance testing
- [ ] Rollback plan ready

### Emergency Procedures

#### Rollback Process

1. **Immediate rollback**:
   ```bash
   gcloud app versions list
   gcloud app services set-traffic default --splits=PREVIOUS_VERSION=1
   ```

2. **Database rollback** (if needed):
   ```bash
   # Restore from backup
   gcloud sql backups restore BACKUP_ID --restore-instance=INSTANCE_NAME
   ```

#### Incident Response

1. **Assess impact**: Check monitoring and logs
2. **Communicate**: Notify stakeholders
3. **Mitigate**: Apply immediate fixes or rollback
4. **Investigate**: Root cause analysis
5. **Document**: Update runbooks and procedures

## Support and Contacts

- **Technical Lead**: [Your Name] - [email]
- **DevOps Team**: [Team Email]
- **On-Call**: [On-call rotation details]
- **Documentation**: [Wiki/Confluence link]

## Additional Resources

- [Google Cloud Documentation](https://cloud.google.com/docs)
- [App Engine Documentation](https://cloud.google.com/appengine/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)