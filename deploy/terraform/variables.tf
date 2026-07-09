variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as prefix for resources"
  type        = string
  default     = "football-manager"
}

variable "image_tag" {
  description = "Docker image tag for ECR images"
  type        = string
  default     = "latest"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "football_manager"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "fm_user"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "fargate_cpu" {
  description = "Fargate CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "fargate_memory" {
  description = "Fargate memory in MB"
  type        = number
  default     = 512
}

variable "cors_origins" {
  description = "Comma-separated CORS origins for the backend"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional)"
  type        = string
  default     = ""
}

variable "jobs_timezone" {
  description = "IANA timezone used to evaluate the scheduled jobs cron expressions"
  type        = string
  default     = "America/Sao_Paulo"
}
