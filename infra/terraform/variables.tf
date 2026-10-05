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