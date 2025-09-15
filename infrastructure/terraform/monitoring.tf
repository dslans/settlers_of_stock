# Monitoring and alerting configuration for Settlers of Stock

# Notification channel for alerts
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notifications"
  type         = "email"
  
  labels = {
    email_address = var.admin_email
  }
  
  depends_on = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "slack" {
  count        = var.slack_webhook_url != "" ? 1 : 0
  display_name = "Slack Notifications"
  type         = "slack"
  
  labels = {
    url = var.slack_webhook_url
  }
  
  depends_on = [google_project_service.apis]
}

# Uptime check for the application
resource "google_monitoring_uptime_check_config" "app_uptime" {
  display_name = "Settlers of Stock App Uptime"
  timeout      = "10s"
  period       = "60s"
  
  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.app_domain
    }
  }
  
  content_matchers {
    content = "healthy"
    matcher = "CONTAINS_STRING"
  }
  
  depends_on = [google_project_service.apis]
}

# Alert policy for uptime check failures
resource "google_monitoring_alert_policy" "uptime_alert" {
  display_name = "Settlers of Stock - Application Down"
  combiner     = "OR"
  
  conditions {
    display_name = "Uptime check failure"
    
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND resource.labels.project_id=\"${var.project_id}\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_FRACTION_TRUE"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.name
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.apis]
}

# Alert policy for high error rate
resource "google_monitoring_alert_policy" "error_rate_alert" {
  display_name = "Settlers of Stock - High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "High 5xx error rate"
    
    condition_threshold {
      filter          = "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/response_count\" AND metric.labels.response_code>=500"
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.name
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.apis]
}

# Alert policy for high response latency
resource "google_monitoring_alert_policy" "latency_alert" {
  display_name = "Settlers of Stock - High Response Latency"
  combiner     = "OR"
  
  conditions {
    display_name = "High response latency"
    
    condition_threshold {
      filter          = "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/response_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 2000  # 2 seconds
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.name
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.apis]
}

# Alert policy for database connection issues
resource "google_monitoring_alert_policy" "database_alert" {
  display_name = "Settlers of Stock - Database Issues"
  combiner     = "OR"
  
  conditions {
    display_name = "High database connection failures"
    
    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/network/connections\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.name
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.apis]
}

# Alert policy for Redis memory usage
resource "google_monitoring_alert_policy" "redis_memory_alert" {
  display_name = "Settlers of Stock - Redis High Memory Usage"
  combiner     = "OR"
  
  conditions {
    display_name = "Redis memory usage > 80%"
    
    condition_threshold {
      filter          = "resource.type=\"redis_instance\" AND metric.type=\"redis.googleapis.com/stats/memory/usage_ratio\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email.name
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  depends_on = [google_project_service.apis]
}

# Custom dashboard for application metrics (disabled for initial deployment)
# Will be enabled after App Engine is deployed
# resource "google_monitoring_dashboard" "app_dashboard" {
#   dashboard_json = jsonencode({
#     displayName = "Settlers of Stock - Application Dashboard"
#     mosaicLayout = {
#       tiles = [
#         {
#           width  = 6
#           height = 4
#           widget = {
#             title = "Request Rate"
#             xyChart = {
#               dataSets = [{
#                 timeSeriesQuery = {
#                   timeSeriesFilter = {
#                     filter = "resource.type=\"gae_app\" AND metric.type=\"appengine.googleapis.com/http/server/request_count\""
#                     aggregation = {
#                       alignmentPeriod    = "60s"
#                       perSeriesAligner   = "ALIGN_RATE"
#                       crossSeriesReducer = "REDUCE_SUM"
#                     }
#                   }
#                 }
#                 plotType = "LINE"
#               }]
#               yAxis = {
#                 label = "Requests/sec"
#                 scale = "LINEAR"
#               }
#             }
#           }
#         }
#       ]
#     }
#   })
#   
#   depends_on = [google_project_service.apis]
# }