# Terraform configuration for Settlers of Stock GCP infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  
  # backend "gcs" {
  #   bucket = "settlers-of-stock-terraform-state"
  #   prefix = "terraform/state"
  # }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Local variables
locals {
  services = [
    "compute.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "appengine.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "firestore.googleapis.com",
    "servicenetworking.googleapis.com"
  ]
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset(local.services)
  project  = var.project_id
  service  = each.value

  disable_dependent_services = false
  disable_on_destroy        = false
}

# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-db-${var.environment}"
  database_version = "POSTGRES_15"
  region          = var.region
  
  settings {
    tier                        = var.db_tier
    availability_type          = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type                  = "PD_SSD"
    disk_size                  = var.db_disk_size
    disk_autoresize           = true
    disk_autoresize_limit     = var.db_max_disk_size
    
    backup_configuration {
      enabled                        = true
      start_time                    = "03:00"
      location                      = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }
    
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    
    maintenance_window {
      day          = 7
      hour         = 3
      update_track = "stable"
    }
  }
  
  deletion_protection = var.environment == "production"
  
  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
}

# Database user
resource "google_sql_user" "user" {
  name     = var.database_user
  instance = google_sql_database_instance.main.name
  password = var.database_password
}

# Cloud Memorystore Redis instance
resource "google_redis_instance" "cache" {
  name           = "${var.project_name}-redis-${var.environment}"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size
  region         = var.region
  
  location_id             = var.zone
  # alternative_location_id not supported for BASIC tier
  
  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  
  redis_version     = "REDIS_7_0"
  display_name      = "Settlers of Stock Redis Cache"
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }
  
  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc-${var.environment}"
  auto_create_subnetworks = false
  mtu                     = 1460
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.project_name}-subnet-${var.environment}"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  
  secondary_ip_range {
    range_name    = "services-range"
    ip_cidr_range = "192.168.1.0/24"
  }
  
  secondary_ip_range {
    range_name    = "pod-ranges"
    ip_cidr_range = "192.168.64.0/22"
  }
}

# Private service access
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Terraform state bucket (for future remote state)
resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud Storage buckets
resource "google_storage_bucket" "frontend" {
  name          = "${var.project_id}-frontend"
  location      = var.region
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
  
  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "exports" {
  name          = "${var.project_id}-exports"
  location      = var.region
  force_destroy = var.environment != "production"
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-backups"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}

# BigQuery dataset for analytics
resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "settlers_of_stock_analytics"
  friendly_name              = "Settlers of Stock Analytics"
  description                = "Dataset for historical market data and analytics"
  location                   = var.region
  default_table_expiration_ms = 3600000 # 1 hour default expiration
  
  access {
    role          = "OWNER"
    user_by_email = var.admin_email
  }
  
  access {
    role         = "READER"
    special_group = "projectReaders"
  }
  
  access {
    role         = "WRITER"
    special_group = "projectWriters"
  }
}

# Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.apis]
}

# IAM Service Account for the application
resource "google_service_account" "app_service_account" {
  account_id   = "settlers-app-prod"
  display_name = "Settlers of Stock Application Service Account"
  description  = "Service account for the Settlers of Stock application"
}

# IAM bindings for the service account
resource "google_project_iam_member" "app_service_account_bindings" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/redis.editor",
    "roles/storage.objectAdmin",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/datastore.user",
    "roles/aiplatform.user",
    "roles/secretmanager.secretAccessor",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# Cloud Build trigger (disabled for initial deployment)
# resource "google_cloudbuild_trigger" "main" {
#   name        = "${var.project_name}-build-${var.environment}"
#   description = "Build and deploy Settlers of Stock application"
#   
#   github {
#     owner = var.github_owner
#     name  = var.github_repo
#     push {
#       branch = var.environment == "production" ? "main" : "develop"
#     }
#   }
#   
#   filename = "cloudbuild.yaml"
#   
#   substitutions = {
#     _ENVIRONMENT = var.environment
#     _GCP_REGION  = var.region
#   }
#   
#   depends_on = [google_project_service.apis]
# }