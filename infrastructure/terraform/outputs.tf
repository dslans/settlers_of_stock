# Terraform outputs for Settlers of Stock infrastructure

output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "The GCP region"
  value       = var.region
}

# Database outputs
output "database_instance_name" {
  description = "The Cloud SQL instance name"
  value       = google_sql_database_instance.main.name
}

output "database_connection_name" {
  description = "The Cloud SQL instance connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "database_private_ip" {
  description = "The Cloud SQL instance private IP"
  value       = google_sql_database_instance.main.private_ip_address
  sensitive   = true
}

output "database_url" {
  description = "The database connection URL"
  value       = "postgresql://${var.database_user}:${var.database_password}@${google_sql_database_instance.main.private_ip_address}:5432/${var.database_name}"
  sensitive   = true
}

# Redis outputs
output "redis_instance_name" {
  description = "The Redis instance name"
  value       = google_redis_instance.cache.name
}

output "redis_host" {
  description = "The Redis instance host"
  value       = google_redis_instance.cache.host
  sensitive   = true
}

output "redis_port" {
  description = "The Redis instance port"
  value       = google_redis_instance.cache.port
}

output "redis_url" {
  description = "The Redis connection URL"
  value       = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
  sensitive   = true
}

# Storage outputs
output "frontend_bucket_name" {
  description = "The frontend storage bucket name"
  value       = google_storage_bucket.frontend.name
}

output "frontend_bucket_url" {
  description = "The frontend storage bucket URL"
  value       = google_storage_bucket.frontend.url
}

output "exports_bucket_name" {
  description = "The exports storage bucket name"
  value       = google_storage_bucket.exports.name
}

output "backups_bucket_name" {
  description = "The backups storage bucket name"
  value       = google_storage_bucket.backups.name
}

# BigQuery outputs
output "bigquery_dataset_id" {
  description = "The BigQuery dataset ID"
  value       = google_bigquery_dataset.analytics.dataset_id
}

# Service account outputs
output "app_service_account_email" {
  description = "The application service account email"
  value       = google_service_account.app_service_account.email
}

# Network outputs
output "vpc_network_name" {
  description = "The VPC network name"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "The subnet name"
  value       = google_compute_subnetwork.subnet.name
}

# Cloud Build outputs (disabled for initial deployment)
# output "cloud_build_trigger_id" {
#   description = "The Cloud Build trigger ID"
#   value       = google_cloudbuild_trigger.main.id
# }