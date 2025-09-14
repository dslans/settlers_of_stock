#!/bin/bash

# Maintenance script for Settlers of Stock production environment
# This script provides common maintenance operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID=""
ENVIRONMENT="production"
REGION="us-central1"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check application health
check_health() {
    print_status "Checking application health..."
    
    APP_URL=$(gcloud app describe --format="value(defaultHostname)" --project="$PROJECT_ID")
    
    # Check health endpoint
    if curl -f "https://$APP_URL/health" 2>/dev/null | grep -q "healthy"; then
        print_success "Application is healthy"
    else
        print_error "Application health check failed"
        return 1
    fi
    
    # Check status endpoint
    STATUS_RESPONSE=$(curl -s "https://$APP_URL/status" 2>/dev/null || echo "")
    if [ -n "$STATUS_RESPONSE" ]; then
        echo "$STATUS_RESPONSE" | jq '.' 2>/dev/null || echo "$STATUS_RESPONSE"
    else
        print_warning "Could not retrieve status information"
    fi
}

# Function to view application logs
view_logs() {
    local LINES=${1:-100}
    print_status "Viewing last $LINES lines of application logs..."
    
    gcloud logging read "resource.type=gae_app AND resource.labels.project_id=$PROJECT_ID" \
        --limit="$LINES" \
        --format="table(timestamp,severity,textPayload)" \
        --project="$PROJECT_ID"
}

# Function to view error logs
view_error_logs() {
    local LINES=${1:-50}
    print_status "Viewing last $LINES error log entries..."
    
    gcloud logging read "resource.type=gae_app AND resource.labels.project_id=$PROJECT_ID AND severity>=ERROR" \
        --limit="$LINES" \
        --format="table(timestamp,severity,textPayload)" \
        --project="$PROJECT_ID"
}

# Function to check database status
check_database() {
    print_status "Checking database status..."
    
    # Get database instance name
    DB_INSTANCE=$(gcloud sql instances list --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$DB_INSTANCE" ]; then
        print_error "No database instance found"
        return 1
    fi
    
    # Check database status
    DB_STATUS=$(gcloud sql instances describe "$DB_INSTANCE" --format="value(state)" --project="$PROJECT_ID")
    print_status "Database instance $DB_INSTANCE status: $DB_STATUS"
    
    # Check database connections
    gcloud sql instances describe "$DB_INSTANCE" \
        --format="table(settings.ipConfiguration.authorizedNetworks[].value:label=AUTHORIZED_NETWORKS,backendType,connectionName)" \
        --project="$PROJECT_ID"
}

# Function to check Redis status
check_redis() {
    print_status "Checking Redis status..."
    
    # Get Redis instance name
    REDIS_INSTANCE=$(gcloud redis instances list --region="$REGION" --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$REDIS_INSTANCE" ]; then
        print_error "No Redis instance found"
        return 1
    fi
    
    # Check Redis status
    gcloud redis instances describe "$REDIS_INSTANCE" \
        --region="$REGION" \
        --format="table(name,state,memorySizeGb,host,port)" \
        --project="$PROJECT_ID"
}

# Function to backup database
backup_database() {
    print_status "Creating database backup..."
    
    DB_INSTANCE=$(gcloud sql instances list --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$DB_INSTANCE" ]; then
        print_error "No database instance found"
        return 1
    fi
    
    BACKUP_ID="manual-backup-$(date +%Y%m%d-%H%M%S)"
    
    gcloud sql backups create \
        --instance="$DB_INSTANCE" \
        --description="Manual backup created by maintenance script" \
        --project="$PROJECT_ID"
    
    print_success "Database backup initiated"
}

# Function to list recent backups
list_backups() {
    print_status "Listing recent database backups..."
    
    DB_INSTANCE=$(gcloud sql instances list --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$DB_INSTANCE" ]; then
        print_error "No database instance found"
        return 1
    fi
    
    gcloud sql backups list \
        --instance="$DB_INSTANCE" \
        --limit=10 \
        --format="table(id,startTime,status,type)" \
        --project="$PROJECT_ID"
}

# Function to scale application
scale_app() {
    local MIN_INSTANCES=${1:-1}
    local MAX_INSTANCES=${2:-10}
    
    print_status "Scaling application (min: $MIN_INSTANCES, max: $MAX_INSTANCES)..."
    
    # Update app.yaml with new scaling settings
    sed -i.bak "s/min_instances: [0-9]*/min_instances: $MIN_INSTANCES/" app.yaml
    sed -i.bak "s/max_instances: [0-9]*/max_instances: $MAX_INSTANCES/" app.yaml
    
    # Deploy with new settings
    gcloud app deploy app.yaml --quiet --project="$PROJECT_ID"
    
    print_success "Application scaled successfully"
}

# Function to view monitoring metrics
view_metrics() {
    print_status "Viewing key application metrics..."
    
    # Request rate (last hour)
    print_status "Request rate (last hour):"
    gcloud logging read "resource.type=gae_app AND resource.labels.project_id=$PROJECT_ID" \
        --freshness=1h \
        --format="value(timestamp)" \
        --project="$PROJECT_ID" | wc -l
    
    # Error rate (last hour)
    print_status "Error count (last hour):"
    gcloud logging read "resource.type=gae_app AND resource.labels.project_id=$PROJECT_ID AND severity>=ERROR" \
        --freshness=1h \
        --format="value(timestamp)" \
        --project="$PROJECT_ID" | wc -l
}

# Function to update secrets
update_secrets() {
    print_status "Updating application secrets..."
    
    echo "Available secrets:"
    gcloud secrets list --filter="name~settlers-of-stock" --format="table(name,createTime)" --project="$PROJECT_ID"
    
    read -p "Enter secret name to update: " SECRET_NAME
    if [ -n "$SECRET_NAME" ]; then
        read -s -p "Enter new secret value: " SECRET_VALUE
        echo
        
        echo "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
        print_success "Secret $SECRET_NAME updated successfully"
    fi
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # This would typically connect to the database and run Alembic migrations
    # For now, we'll show how to connect to the database
    
    DB_INSTANCE=$(gcloud sql instances list --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$DB_INSTANCE" ]; then
        print_error "No database instance found"
        return 1
    fi
    
    print_status "To run migrations manually, connect to the database:"
    echo "gcloud sql connect $DB_INSTANCE --user=app_user --project=$PROJECT_ID"
    echo "Then run: alembic upgrade head"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  health                   Check application health"
    echo "  logs [LINES]            View application logs (default: 100 lines)"
    echo "  errors [LINES]          View error logs (default: 50 lines)"
    echo "  database                Check database status"
    echo "  redis                   Check Redis status"
    echo "  backup                  Create database backup"
    echo "  backups                 List recent backups"
    echo "  scale MIN MAX           Scale application instances"
    echo "  metrics                 View key metrics"
    echo "  secrets                 Update application secrets"
    echo "  migrations              Run database migrations"
    echo ""
    echo "Options:"
    echo "  --project-id ID         Set GCP project ID"
    echo "  --environment ENV       Set environment (default: production)"
    echo "  --help                  Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        health)
            check_health
            exit 0
            ;;
        logs)
            view_logs "$2"
            exit 0
            ;;
        errors)
            view_error_logs "$2"
            exit 0
            ;;
        database)
            check_database
            exit 0
            ;;
        redis)
            check_redis
            exit 0
            ;;
        backup)
            backup_database
            exit 0
            ;;
        backups)
            list_backups
            exit 0
            ;;
        scale)
            scale_app "$2" "$3"
            exit 0
            ;;
        metrics)
            view_metrics
            exit 0
            ;;
        secrets)
            update_secrets
            exit 0
            ;;
        migrations)
            run_migrations
            exit 0
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
done

# If no command provided, show usage
show_usage