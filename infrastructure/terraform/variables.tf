# Terraform variables for Settlers of Stock infrastructure

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The project name for resource naming"
  type        = string
  default     = "settlers-of-stock"
}

variable "environment" {
  description = "The environment (development, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "alternative_zone" {
  description = "Alternative GCP zone for high availability"
  type        = string
  default     = "us-central1-b"
}

# Database variables
variable "database_name" {
  description = "The name of the database"
  type        = string
  default     = "settlers_of_stock"
}

variable "database_user" {
  description = "The database user name"
  type        = string
  default     = "app_user"
}

variable "database_password" {
  description = "The database password"
  type        = string
  sensitive   = true
}

variable "db_tier" {
  description = "The database instance tier"
  type        = string
  default     = "db-f1-micro"
  
  validation {
    condition = contains([
      "db-f1-micro", "db-g1-small", "db-n1-standard-1", 
      "db-n1-standard-2", "db-n1-standard-4", "db-n1-standard-8"
    ], var.db_tier)
    error_message = "Database tier must be a valid Cloud SQL tier."
  }
}

variable "db_disk_size" {
  description = "The database disk size in GB"
  type        = number
  default     = 20
}

variable "db_max_disk_size" {
  description = "The maximum database disk size in GB"
  type        = number
  default     = 100
}

# Redis variables
variable "redis_tier" {
  description = "The Redis instance tier"
  type        = string
  default     = "STANDARD_HA"
  
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be either BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size" {
  description = "The Redis memory size in GB"
  type        = number
  default     = 1
}

# GitHub variables for Cloud Build
variable "github_owner" {
  description = "The GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "The GitHub repository name"
  type        = string
  default     = "settlers-of-stock"
}

# Admin email for BigQuery access
variable "admin_email" {
  description = "Admin email for BigQuery dataset access"
  type        = string
}

# Secret variables
variable "app_secret_key" {
  description = "The application secret key for JWT signing"
  type        = string
  sensitive   = true
}

variable "alpha_vantage_api_key" {
  description = "Alpha Vantage API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "news_api_key" {
  description = "News API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "reddit_client_id" {
  description = "Reddit API client ID"
  type        = string
  sensitive   = true
  default     = ""
}

variable "reddit_client_secret" {
  description = "Reddit API client secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_host" {
  description = "SMTP server host"
  type        = string
  default     = ""
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = number
  default     = 587
}

variable "smtp_user" {
  description = "SMTP username"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_password" {
  description = "SMTP password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_tls" {
  description = "Enable SMTP TLS"
  type        = bool
  default     = true
}

# Monitoring variables
variable "app_domain" {
  description = "The application domain for uptime monitoring"
  type        = string
  default     = "settlers-of-stock.com"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
  default     = ""
}