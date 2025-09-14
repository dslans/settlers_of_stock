# Secret Manager configuration for Settlers of Stock

# Application secrets
resource "google_secret_manager_secret" "app_secrets" {
  secret_id = "${var.project_name}-app-secrets-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "app_secrets" {
  secret = google_secret_manager_secret.app_secrets.id
  secret_data = jsonencode({
    secret_key                  = var.app_secret_key
    jwt_algorithm               = "HS256"
    access_token_expire_minutes = 30
    refresh_token_expire_days   = 7
  })
}

# Database connection secrets
resource "google_secret_manager_secret" "database_url" {
  secret_id = "${var.project_name}-database-url-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://${var.database_user}:${var.database_password}@${google_sql_database_instance.main.private_ip_address}:5432/${var.database_name}"

  depends_on = [google_sql_database_instance.main]
}

# Redis connection secrets
resource "google_secret_manager_secret" "redis_url" {
  secret_id = "${var.project_name}-redis-url-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "redis_url" {
  secret      = google_secret_manager_secret.redis_url.id
  secret_data = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"

  depends_on = [google_redis_instance.cache]
}

# External API keys
resource "google_secret_manager_secret" "api_keys" {
  secret_id = "${var.project_name}-api-keys-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "api_keys" {
  secret = google_secret_manager_secret.api_keys.id
  secret_data = jsonencode({
    alpha_vantage = var.alpha_vantage_api_key
    news_api      = var.news_api_key
  })
}

# Reddit API credentials
resource "google_secret_manager_secret" "reddit_credentials" {
  secret_id = "${var.project_name}-reddit-credentials-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "reddit_credentials" {
  secret = google_secret_manager_secret.reddit_credentials.id
  secret_data = jsonencode({
    client_id     = var.reddit_client_id
    client_secret = var.reddit_client_secret
  })
}

# SMTP configuration
resource "google_secret_manager_secret" "smtp_config" {
  secret_id = "${var.project_name}-smtp-config-${var.environment}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "smtp_config" {
  secret = google_secret_manager_secret.smtp_config.id
  secret_data = jsonencode({
    host     = var.smtp_host
    port     = var.smtp_port
    user     = var.smtp_user
    password = var.smtp_password
    tls      = var.smtp_tls
  })
}

# IAM bindings for secret access
resource "google_secret_manager_secret_iam_member" "app_secrets_access" {
  for_each = toset([
    google_secret_manager_secret.app_secrets.secret_id,
    google_secret_manager_secret.database_url.secret_id,
    google_secret_manager_secret.redis_url.secret_id,
    google_secret_manager_secret.api_keys.secret_id,
    google_secret_manager_secret.reddit_credentials.secret_id,
    google_secret_manager_secret.smtp_config.secret_id
  ])

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}
