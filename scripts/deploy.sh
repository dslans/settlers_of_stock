#!/bin/bash

# Deployment script for Settlers of Stock
# This script handles deployment to Google Cloud Platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="settlers-of-stock"
ENVIRONMENT="production"
REGION="us-central1"
GITHUB_OWNER="dslans"
GITHUB_REPO="settlers-of-stock"

# Function to print colored output
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

# Function to check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to validate configuration
validate_config() {
    print_status "Validating configuration..."
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "PROJECT_ID is not set. Please configure it in this script."
        exit 1
    fi
    
    if [ -z "$GITHUB_OWNER" ]; then
        print_error "GITHUB_OWNER is not set. Please configure it in this script."
        exit 1
    fi
    
    # Set the project
    gcloud config set project "$PROJECT_ID"
    
    print_success "Configuration validated"
}

# Function to deploy infrastructure with Terraform
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    cd infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars if it doesn't exist
    if [ ! -f terraform.tfvars ]; then
        print_warning "terraform.tfvars not found. Creating template..."
        cat > terraform.tfvars << EOF
project_id = "$PROJECT_ID"
environment = "$ENVIRONMENT"
region = "$REGION"
github_owner = "$GITHUB_OWNER"
github_repo = "$GITHUB_REPO"
admin_email = "admin@example.com"

# Database configuration
database_password = "$(openssl rand -base64 32)"
db_tier = "db-f1-micro"

# Secrets (replace with actual values)
app_secret_key = "$(openssl rand -base64 64)"
alpha_vantage_api_key = ""
news_api_key = ""
reddit_client_id = ""
reddit_client_secret = ""
smtp_host = ""
smtp_user = ""
smtp_password = ""
EOF
        print_warning "Please edit terraform.tfvars with your actual values before continuing."
        read -p "Press Enter to continue after editing terraform.tfvars..."
    fi
    
    # Plan the deployment
    terraform plan -out=tfplan
    
    # Ask for confirmation
    read -p "Do you want to apply these changes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply tfplan
        print_success "Infrastructure deployed successfully"
    else
        print_warning "Deployment cancelled"
        exit 0
    fi
    
    cd ../..
}

# Function to build and deploy the application
deploy_application() {
    print_status "Deploying application..."
    
    # Enable required APIs
    print_status "Enabling required APIs..."
    gcloud services enable \
        appengine.googleapis.com \
        cloudbuild.googleapis.com \
        secretmanager.googleapis.com \
        sqladmin.googleapis.com \
        redis.googleapis.com \
        storage.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com \
        aiplatform.googleapis.com \
        bigquery.googleapis.com \
        firestore.googleapis.com
    
    # Create App Engine application if it doesn't exist
    if ! gcloud app describe &> /dev/null; then
        print_status "Creating App Engine application..."
        gcloud app create --region="$REGION"
    fi
    
    # Deploy using Cloud Build
    print_status "Starting Cloud Build deployment..."
    gcloud builds submit --config=cloudbuild.yaml \
        --substitutions=_ENVIRONMENT="$ENVIRONMENT",_GCP_REGION="$REGION"
    
    print_success "Application deployed successfully"
}

# Function to run post-deployment checks
post_deployment_checks() {
    print_status "Running post-deployment checks..."
    
    # Get the App Engine URL
    APP_URL=$(gcloud app describe --format="value(defaultHostname)")
    
    # Check health endpoint
    print_status "Checking health endpoint..."
    if curl -f "https://$APP_URL/health" > /dev/null 2>&1; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        exit 1
    fi
    
    # Check status endpoint
    print_status "Checking status endpoint..."
    if curl -f "https://$APP_URL/status" > /dev/null 2>&1; then
        print_success "Status check passed"
    else
        print_warning "Status check failed - application may be starting up"
    fi
    
    print_success "Post-deployment checks completed"
    print_success "Application is available at: https://$APP_URL"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --infrastructure-only    Deploy only infrastructure (Terraform)"
    echo "  --application-only       Deploy only application (skip infrastructure)"
    echo "  --environment ENV        Set environment (default: production)"
    echo "  --project-id ID          Set GCP project ID"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Full deployment"
    echo "  $0 --infrastructure-only             # Deploy only infrastructure"
    echo "  $0 --application-only                # Deploy only application"
    echo "  $0 --environment staging             # Deploy to staging"
}

# Parse command line arguments
INFRASTRUCTURE_ONLY=false
APPLICATION_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --infrastructure-only)
            INFRASTRUCTURE_ONLY=true
            shift
            ;;
        --application-only)
            APPLICATION_ONLY=true
            shift
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    print_status "Starting Settlers of Stock deployment..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Project ID: $PROJECT_ID"
    
    check_prerequisites
    validate_config
    
    if [ "$APPLICATION_ONLY" = false ]; then
        deploy_infrastructure
    fi
    
    if [ "$INFRASTRUCTURE_ONLY" = false ]; then
        deploy_application
        post_deployment_checks
    fi
    
    print_success "Deployment completed successfully!"
}

# Run main function
main "$@"