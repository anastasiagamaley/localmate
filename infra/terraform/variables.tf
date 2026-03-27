variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "eu-central-1"   # Frankfurt — closest to Slovakia
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "localmate"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "JWT secret key — long random string"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

variable "docker_image_tag" {
  description = "Docker image tag to deploy (e.g. git SHA)"
  type        = string
  default     = "latest"
}

variable "docker_registry" {
  description = "Docker registry prefix (e.g. your Docker Hub username)"
  type        = string
}
