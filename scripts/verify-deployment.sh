#!/bin/bash

# Deployment verification script for Settlers of Stock
# This script verifies that the deployment was successful

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

# Function to verify App Engine deployment
verify_app_engine() {
    print_status "Verifying App Engine deployment..."
    
    # Check if App Engine app exists
    if ! gcloud app describe --project="$PROJECT_ID" &> /dev/null; then
        print_error "App Engine application not found"
        return 1
    fi
    
    # Get app URL
    APP_URL=$(gcloud app describe --format="value(defaultHostname)" --project="$PROJECT_ID")
    print_status "Application URL: https://$APP_URL"
    
    # Test health endpoint
    if curl -f -s "https://$APP_URL/health" | grep -q "healthy"; then
        print_success "Health endpoint is responding correctly"
    else
        print_error "Health endpoint is not responding correctly"
        return 1
    fi
    
    # Test status endpoint
    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$APP_URL/status")
    if [ "$STATUS_CODE" = "200" ]; then
        print_success "Status endpoint is responding correctly"
    else
        print_warning "Status endpoint returned HTTP $STATUS_CODE"
    fi
    
    # Test API endpoints
    API_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$APP_URL/api/v1/")
    if [ "$API_CODE" = "404" ] || [ "$API_CODE" = "200" ]; then
        print_success "API endpoints are accessible"
    else
        print_warning "API endpoints may not be working correctly (HTTP $API_CODE)"
    fi
}

# Function to verify database
verify_database() {
    print_status "Verifying database deployment..."
    
    # Check if database instance exists
    DB_INSTANCE=$(gcloud sql instances list --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$DB_INSTANCE" ]; then
        print_error "Database instance not found"
        return 1
    fi
    
    # Check database status
    DB_STATUS=$(gcloud sql instances describe "$DB_INSTANCE" --format="value(state)" --project="$PROJECT_ID")
    if [ "$DB_STATUS" = "RUNNABLE" ]; then
        print_success "Database instance is running"
    else
        print_error "Database instance status: $DB_STATUS"
        return 1
    fi
    
    # Check if database exists
    DB_LIST=$(gcloud sql databases list --instance="$DB_INSTANCE" --format="value(name)" --project="$PROJECT_ID")
    if echo "$DB_LIST" | grep -q "settlers_of_stock"; then
        print_success "Application database exists"
    else
        print_error "Application database not found"
        return 1
    fi
}

# Function to verify Redis
verify_redis() {
    print_status "Verifying Redis deployment..."
    
    # Check if Redis instance exists
    REDIS_INSTANCE=$(gcloud redis instances list --region="us-central1" --format="value(name)" --filter="name~settlers-of-stock" --project="$PROJECT_ID" | head -n1)
    
    if [ -z "$REDIS_INSTANCE" ]; then
        print_error "Redis instance not found"
        return 1
    fi
    
    # Check Redis status
    REDIS_STATUS=$(gcloud redis instances describe "$REDIS_INSTANCE" --region="us-central1" --format="value(state)" --project="$PROJECT_ID")
    if [ "$REDIS_STATUS" = "READY" ]; then
        print_success "Redis instance is ready"
    else
        print_error "Redis instance status: $REDIS_STATUS"
        return 1
    fi
}

# Function to verify storage buckets
verify_storage() {
    print_status "Verifying storage buckets..."
    
    # Check frontend bucket
    if gsutil ls "gs://$PROJECT_ID-frontend/" &> /dev/null; then
        print_success "Frontend storage bucket exists"
    else
        print_error "Frontend storage bucket not found"
        return 1
    fi
    
    # Check exports bucket
    if gsutil ls "gs://$PROJECT_ID-exports/" &> /dev/null; then
        print_success "Exports storage bucket exists"
    else
        print_warning "Exports storage bucket not found"
    fi
    
    # Check backups bucket
    if gsutil ls "gs://$PROJECT_ID-backups/" &> /dev/null; then
        print_success "Backups storage bucket exists"
    else
        print_warning "Backups storage bucket not found"
    fi
}

# Function to verify secrets
verify_secrets() {
    print_status "Verifying secrets..."
    
    # List secrets
    SECRETS=$(gcloud secrets list --filter="name~settlers-of-stock" --format="value(name)" --project="$PROJECT_ID")
    
    if [ -z "$SECRETS" ]; then
        print_error "No application secrets found"
        return 1
    fi
    
    SECRET_COUNT=$(echo "$SECRETS" | wc -l)
    print_success "Found $SECRET_COUNT application secrets"
    
    # Check if key secrets exist
    REQUIRED_SECRETS=("app-secrets" "database-url" "redis-url")
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if echo "$SECRETS" | grep -q "$secret"; then
            print_success "Secret $secret exists"
        else
            print_error "Required secret $secret not found"
            return 1
        fi
    done
}

# Function to verify monitoring
verify_monitoring() {
    print_status "Verifying monitoring setup..."
    
    # Check if uptime check exists
    UPTIME_CHECKS=$(gcloud monitoring uptime list --format="value(name)" --project="$PROJECT_ID" | grep -c "settlers-of-stock" || true)
    
    if [ "$UPTIME_CHECKS" -gt 0 ]; then
        print_success "Uptime monitoring is configured"
    else
        print_warning "No uptime checks found"
    fi
    
    # Check alert policies
    ALERT_POLICIES=$(gcloud alpha monitoring policies list --format="value(name)" --filter="displayName~'Settlers of Stock'" --project="$PROJECT_ID" | wc -l)
    
    if [ "$ALERT_POLICIES" -gt 0 ]; then
        print_success "Alert policies are configured"
    else
        print_warning "No alert policies found"
    fi
}

# Function to verify BigQuery
verify_bigquery() {
    print_status "Verifying BigQuery setup..."
    
    # Check if dataset exists
    if bq ls --project_id="$PROJECT_ID" | grep -q "settlers_of_stock_analytics"; then
        print_success "BigQuery dataset exists"
    else
        print_error "BigQuery dataset not found"
        return 1
    fi
}

# Function to verify Firestore
verify_firestore() {
    print_status "Verifying Firestore setup..."
    
    # Check if Firestore is enabled
    if gcloud firestore databases describe --database="(default)" --project="$PROJECT_ID" &> /dev/null; then
        print_success "Firestore database is configured"
    else
        print_error "Firestore database not found"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running basic performance tests..."
    
    APP_URL=$(gcloud app describe --format="value(defaultHostname)" --project="$PROJECT_ID")
    
    # Test response time
    RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" "https://$APP_URL/health")
    
    if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
        print_success "Health endpoint response time: ${RESPONSE_TIME}s"
    else
        print_warning "Health endpoint response time is slow: ${RESPONSE_TIME}s"
    fi
    
    # Test multiple concurrent requests
    print_status "Testing concurrent requests..."
    for i in {1..5}; do
        curl -s "https://$APP_URL/health" > /dev/null &
    done
    wait
    print_success "Concurrent request test completed"
}

# Main verification function
main() {
    print_status "Starting deployment verification for Settlers of Stock..."
    print_status "Project: $PROJECT_ID"
    print_status "Environment: $ENVIRONMENT"
    
    FAILED_CHECKS=0
    
    # Run all verification checks
    verify_app_engine || ((FAILED_CHECKS++))
    verify_database || ((FAILED_CHECKS++))
    verify_redis || ((FAILED_CHECKS++))
    verify_storage || ((FAILED_CHECKS++))
    verify_secrets || ((FAILED_CHECKS++))
    verify_monitoring || ((FAILED_CHECKS++))
    verify_bigquery || ((FAILED_CHECKS++))
    verify_firestore || ((FAILED_CHECKS++))
    
    # Run performance tests
    run_performance_tests
    
    # Summary
    echo ""
    if [ $FAILED_CHECKS -eq 0 ]; then
        print_success "All verification checks passed! Deployment is successful."
        print_status "Application is ready for use."
    else
        print_error "$FAILED_CHECKS verification checks failed."
        print_error "Please review the errors above and fix any issues."
        exit 1
    fi
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
            echo "Usage: $0 --project-id PROJECT_ID [--environment ENV]"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
    print_error "PROJECT_ID is required. Use --project-id flag."
    exit 1
fi

# Set gcloud project
gcloud config set project "$PROJECT_ID"

# Run main verification
main