variable "repository_names" {
  description = "List of ECR repository names"
  type        = list(string)
  default     = [
    "opencapif/api-invoker-management-api", 
    "opencapif/api-provider-management-api", 
    "opencapif/auditing-api",
    "opencapif/auditing-api",
    "opencapif/discover-service-api",
    "opencapif/events-api",
    "opencapif/api-invocation-logs-api",
    "opencapif/publish-service-api",
    "opencapif/routing-info-api",
    "opencapif/security-api",
    "opencapif/nginx",
    "opencapif/jwtauth",
    "opencapif/access-control-policy",
    "opencapif/client"
    ]
}