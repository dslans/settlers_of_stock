# Settlers of Stock - Production Setup Guide

This guide provides step-by-step instructions for setting up the Settlers of Stock application in a production environment on Google Cloud Platform.

## Quick Start

For experienced users who want to deploy quickly:

```bash
# 1. Configure your project
export PROJECT_ID="your-gcp-project-id"
export GITHUB_OWNER="your-github-username"

# 2. Edit deployment configuration
vim scripts/deploy.sh  # Update PROJECT_ID and GITHUB_OWNER

# 3. Create Terraform variables
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
vim infrastructure/terraform/terraform.tfvars  # Update with your values

# 4. Deploy everything
./scripts/deploy.sh

# 5. Verify deployment
./scripts/verify-deployment.sh --project-id $PROJECT_ID
```

## Detailed Setup Instructions

### Step 1: Prerequisites

1. **Install required tools:**
   ```bash
   # Google Cloud SDK
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Terraform
   brew install terraform  # macOS
   # or download from https://terraform.io/downloads
   
   # Other tools
   brew install jq curl  # macOS
   ```

2. **Set up GCP project:**
   ```bash
   # Create new project (optional)
   gcloud projects create settlers-of-stock-prod --name="Settlers of Stock Production"
   
   # Set project
   gcloud config set project settlers-of-stock-prod
   
   # Enable billing
   # Go to https://console.cloud.google.com/billing and link your project
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

### Step 2: Configure Deployment

1. **Update deployment script:**
   ```bash
   vim scripts/deploy.sh
   ```
   
   Set these variables:
   ```bash
   PROJECT_ID="settlers-of-stock-prod"
   GITHUB_OWNER="your-github-username"
   GITHUB_REPO="settlers-of-stock"
   ```

2. **Create Terraform configuration:**
   ```bash
   cd infrastructure/terraform
   cp terraform.tfvars.example terraform.tfvars
   vim terraform.tfvars
   ```
   
   Update with your values:
   ```hcl
   project_id = "settlers-of-stock-prod"
   environment = "production"
   region = "us-central1"
   github_owner = "your-github-username"
   admin_email = "admin@yourdomain.com"
   
   # Generate secure passwords
   database_password = "$(openssl rand -base64 32)"
   app_secret_key = "$(openssl rand -base64 64)"
   
   # Optional: Add your API keys
   alpha_vantage_api_key = "your-key-here"
   news_api_key = "your-key-here"
   ```

### Step 3: Deploy Infrastructure

1. **Deploy with script (recommended):**
   ```bash
   ./scripts/deploy.sh --infrastructure-only
   ```

2. **Or deploy manually:**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```

This creates:
- Cloud SQL PostgreSQL database
- Cloud Memorystore Redis cache
- Cloud Storage buckets
- BigQuery dataset
- Firestore database
- VPC network
- IAM service accounts
- Secret Manager secrets
- Monitoring and alerting

### Step 4: Deploy Application

1. **Deploy with script:**
   ```bash
   ./scripts/deploy.sh --application-only
   ```

2. **Or deploy manually:**
   ```bash
   # Build and test
   cd backend
   uv pip install -r requirements.txt
   python -m pytest tests/ -v
   
   cd ../frontend
   npm ci
   npm run test:ci
   npm run build
   
   # Deploy backend
   cd ../backend
   gcloud app deploy app.yaml --project=settlers-of-stock-prod
   
   # Deploy frontend
   gsutil -m rsync -r -d ../frontend/build/ gs://settlers-of-stock-prod-frontend/
   ```

### Step 5: Verify Deployment

```bash
./scripts/verify-deployment.sh --project-id settlers-of-stock-prod
```

This checks:
- App Engine deployment
- Database connectivity
- Redis availability
- Storage buckets
- Secret Manager
- Monitoring setup
- Performance metrics

### Step 6: Configure Domain (Optional)

1. **Set up custom domain:**
   ```bash
   gcloud app domain-mappings create yourdomain.com --project=settlers-of-stock-prod
   ```

2. **Configure DNS:**
   - Add CNAME record pointing to `ghs.googlehosted.com`
   - Wait for SSL certificate provisioning

3. **Update CORS settings:**
   ```bash
   # Update terraform.tfvars
   cors_origins = ["https://yourdomain.com", "https://www.yourdomain.com"]
   
   # Redeploy
   ./scripts/deploy.sh --application-only
   ```

## Environment-Specific Configurations

### Production Environment

- **Scaling**: Auto-scaling from 1-10 instances
- **Database**: Regional availability, automated backups
- **Redis**: Standard HA tier for high availability
- **Monitoring**: Full monitoring and alerting
- **Security**: Private networking, encrypted storage

### Staging Environment

To set up a staging environment:

```bash
# Create staging project
gcloud projects create settlers-of-stock-staging

# Update configuration
export ENVIRONMENT="staging"
vim infrastructure/terraform/terraform.tfvars  # Set environment = "staging"

# Deploy
./scripts/deploy.sh --environment staging
```

## Security Configuration

### API Keys and Secrets

All sensitive data is stored in Google Secret Manager:

```bash
# View secrets
gcloud secrets list --filter="name~settlers-of-stock"

# Update a secret
echo "new-secret-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Access secret in application (automatic)
# See backend/app/core/config.py for implementation
```

### Network Security

- Database and Redis use private IP addresses
- VPC peering for secure communication
- SSL/TLS enforced for all connections
- Firewall rules restrict access

### Access Control

- Service accounts with minimal permissions
- IAM roles follow principle of least privilege
- Audit logging enabled for all resources

## Monitoring and Maintenance

### Health Monitoring

The application provides several monitoring endpoints:

- `GET /health` - Basic health check
- `GET /status` - Detailed status with dependencies
- Custom metrics sent to Cloud Monitoring

### Maintenance Operations

```bash
# Check application health
./scripts/maintenance.sh health

# View logs
./scripts/maintenance.sh logs 100

# Create database backup
./scripts/maintenance.sh backup

# Scale application
./scripts/maintenance.sh scale 2 20

# Update secrets
./scripts/maintenance.sh secrets
```

### Monitoring Dashboard

Access monitoring at:
- Google Cloud Console → Monitoring
- Custom dashboard: "Settlers of Stock - Application Dashboard"

### Alerts

Configured alerts for:
- Application downtime (uptime check failures)
- High error rates (>10 errors/minute)
- High latency (>2 seconds 95th percentile)
- Database connection issues
- Redis memory usage (>80%)

## Backup and Recovery

### Automated Backups

- **Database**: Daily automated backups, 30-day retention
- **Application Code**: Git repository
- **Configuration**: Terraform state in Cloud Storage

### Manual Backup

```bash
# Create database backup
./scripts/maintenance.sh backup

# Export Terraform state
cd infrastructure/terraform
terraform state pull > backup-$(date +%Y%m%d).tfstate
```

### Recovery Procedures

1. **Application rollback:**
   ```bash
   gcloud app versions list
   gcloud app services set-traffic default --splits=PREVIOUS_VERSION=1
   ```

2. **Database restore:**
   ```bash
   gcloud sql backups list --instance=INSTANCE_NAME
   gcloud sql backups restore BACKUP_ID --restore-instance=INSTANCE_NAME
   ```

3. **Infrastructure recovery:**
   ```bash
   cd infrastructure/terraform
   terraform apply -auto-approve
   ```

## Performance Optimization

### Scaling Configuration

Adjust scaling in `backend/app.yaml`:

```yaml
automatic_scaling:
  min_instances: 2      # Increase for better availability
  max_instances: 50     # Increase for higher load
  target_cpu_utilization: 0.6
  target_throughput_utilization: 0.6
```

### Database Optimization

- Monitor query performance in Cloud SQL
- Add indexes for frequently queried columns
- Consider read replicas for high read loads

### Caching Strategy

- Redis cache for API responses
- Browser caching for static assets
- CDN for global content delivery

## Cost Optimization

### Resource Sizing

- **App Engine**: Start with F2 instances, scale as needed
- **Database**: db-f1-micro for development, db-n1-standard-1+ for production
- **Redis**: 1GB memory for basic caching, scale up as needed

### Cost Monitoring

```bash
# View current costs
gcloud billing budgets list

# Set up budget alerts
gcloud billing budgets create --billing-account=ACCOUNT_ID --budget-file=budget.yaml
```

### Optimization Tips

- Use preemptible instances for batch jobs
- Set up lifecycle policies for storage buckets
- Monitor and optimize BigQuery usage
- Use committed use discounts for predictable workloads

## Troubleshooting

### Common Issues

1. **Deployment fails with permission errors:**
   ```bash
   # Check IAM permissions
   gcloud projects get-iam-policy PROJECT_ID
   
   # Add required roles
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="user:your-email@domain.com" \
     --role="roles/editor"
   ```

2. **Database connection timeouts:**
   ```bash
   # Check VPC connectivity
   gcloud compute networks list
   gcloud sql instances describe INSTANCE_NAME
   
   # Verify private service access
   gcloud services vpc-peerings list --network=VPC_NAME
   ```

3. **High memory usage:**
   ```bash
   # Check instance metrics
   gcloud app instances list
   
   # Scale up instance class
   # Edit app.yaml: instance_class: F4
   gcloud app deploy
   ```

### Debug Commands

```bash
# Application logs
gcloud logging read "resource.type=gae_app" --limit=100

# Database logs
gcloud logging read "resource.type=cloudsql_database" --limit=50

# Build logs
gcloud builds list --limit=10
gcloud builds log BUILD_ID

# Connect to database
gcloud sql connect INSTANCE_NAME --user=app_user

# Test Redis connection
gcloud redis instances describe INSTANCE_NAME --region=us-central1
```

## Support and Documentation

### Getting Help

- **Documentation**: See `DEPLOYMENT.md` for detailed deployment guide
- **Issues**: Create GitHub issues for bugs and feature requests
- **Monitoring**: Check Cloud Console for system status

### Useful Links

- [Google Cloud Console](https://console.cloud.google.com)
- [App Engine Documentation](https://cloud.google.com/appengine/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

### Emergency Contacts

- **Technical Lead**: [Your Name] - [email]
- **DevOps Team**: [Team Email]
- **On-Call**: [Phone/Slack]

---

## Next Steps

After successful deployment:

1. **Configure monitoring alerts** for your team
2. **Set up CI/CD pipeline** for automated deployments
3. **Configure backup retention** policies
4. **Set up staging environment** for testing
5. **Document operational procedures** for your team
6. **Plan capacity scaling** based on usage patterns
7. **Set up cost monitoring** and budgets
8. **Configure security scanning** and compliance checks

Congratulations! Your Settlers of Stock application is now running in production on Google Cloud Platform.