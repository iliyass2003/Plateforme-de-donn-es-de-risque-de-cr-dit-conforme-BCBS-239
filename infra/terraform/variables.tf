variable "minio_endpoint" {
  description = "Adresse de l'API MinIO vue depuis Windows"
  type        = string
  default     = "localhost:9010"
}

variable "minio_user" {
  description = "Compte administrateur MinIO (lu depuis l'environnement)"
  type        = string
}

variable "minio_password" {
  description = "Mot de passe administrateur MinIO (lu depuis l'environnement)"
  type        = string
  sensitive   = true
}

variable "bucket_landing" {
  description = "Nom du bucket de la zone landing"
  type        = string
  default     = "landing"
}
variable "pg_host" {
  description = "Hôte PostgreSQL vu depuis Windows"
  type        = string
  default     = "localhost"
}

variable "pg_port" {
  description = "Port PostgreSQL vu depuis Windows"
  type        = number
  default     = 5440
}

variable "pg_database" {
  description = "Base du warehouse"
  type        = string
  default     = "credit_risk"
}

variable "pg_user" {
  description = "Administrateur PostgreSQL (lu depuis l'environnement)"
  type        = string
}

variable "pg_password" {
  description = "Mot de passe administrateur PostgreSQL (lu depuis l'environnement)"
  type        = string
  sensitive   = true
}
