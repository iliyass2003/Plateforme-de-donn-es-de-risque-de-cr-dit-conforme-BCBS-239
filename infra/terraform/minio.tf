provider "minio" {
  minio_server   = var.minio_endpoint
  minio_user     = var.minio_user
  minio_password = var.minio_password
  minio_ssl      = false
}

# Zone landing : copie exacte des fichiers reçus (BCBS 239 - P3)
resource "minio_s3_bucket" "landing" {
  bucket = var.bucket_landing
}

# Versioning : aucune version d'un objet n'est jamais perdue
resource "minio_s3_bucket_versioning" "landing" {
  bucket = minio_s3_bucket.landing.bucket

  versioning_configuration {
    status = "Enabled"
  }
}