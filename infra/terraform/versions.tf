terraform {
  required_version = ">= 1.6"

  required_providers {
    minio = {
      source  = "aminueza/minio"
      version = "~> 3.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~> 1.25"
    }
  }
}