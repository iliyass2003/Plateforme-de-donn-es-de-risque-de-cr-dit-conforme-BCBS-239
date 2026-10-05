# IMPORTANT : appliquer avec -parallelism=1. Plusieurs droits sur un meme schema
# ne peuvent pas etre ecrits en parallele (erreur PostgreSQL 'tuple concurrently updated').

provider "postgresql" {
  host     = var.pg_host
  port     = var.pg_port
  database = var.pg_database
  username = var.pg_user
  password = var.pg_password
  sslmode  = "disable"
}

locals {
  # Les 5 zones du warehouse (docs/architecture.md)
  schemas = ["bronze", "staging", "intermediate", "marts", "ctl"]

  # Les 6 profils de droits (BCBS 239 - P11)
  roles = [
    "role_ingestion",
    "role_transformation",
    "role_analyste_risque",
    "role_bi",
    "role_auditeur",
    "role_data_scientist",
  ]

  # Qui écrit où
  ecriture = [
    { role = "role_ingestion", schema = "bronze" },
    { role = "role_ingestion", schema = "ctl" },
    { role = "role_transformation", schema = "staging" },
    { role = "role_transformation", schema = "intermediate" },
    { role = "role_transformation", schema = "marts" },
    { role = "role_transformation", schema = "ctl" },
  ]

  # Qui lit quoi, et les tables créées par quel rôle (owner)
  lecture = [
    { role = "role_transformation", schema = "bronze", owner = "role_ingestion" },
    { role = "role_analyste_risque", schema = "marts", owner = "role_transformation" },
    { role = "role_bi", schema = "marts", owner = "role_transformation" },
    { role = "role_data_scientist", schema = "marts", owner = "role_transformation" },
    { role = "role_auditeur", schema = "marts", owner = "role_transformation" },
    { role = "role_auditeur", schema = "ctl", owner = "role_ingestion" },
    { role = "role_auditeur", schema = "ctl", owner = "role_transformation" },
  ]
}

resource "postgresql_schema" "zones" {
  for_each = toset(local.schemas)
  name     = each.key
}

resource "postgresql_role" "profils" {
  for_each = toset(local.roles)
  name     = each.key
  login    = false
}

# Droit d'entrer et de créer des tables dans les schémas d'écriture
resource "postgresql_grant" "ecriture" {
  for_each    = { for e in local.ecriture : "${e.role}.${e.schema}" => e }
  database    = var.pg_database
  role        = each.value.role
  schema      = each.value.schema
  object_type = "schema"
  privileges  = ["USAGE", "CREATE"]
  depends_on  = [postgresql_role.profils, postgresql_schema.zones]
}

# Droit d'entrer dans les schémas de lecture
resource "postgresql_grant" "acces_lecture" {
  for_each    = { for l in local.lecture : "${l.role}.${l.schema}" => l.schema... }
  database    = var.pg_database
  role        = split(".", each.key)[0]
  schema      = each.value[0]
  object_type = "schema"
  privileges  = ["USAGE"]
  depends_on  = [postgresql_role.profils, postgresql_schema.zones]
}

# Lecture automatique de toutes les tables futures
resource "postgresql_default_privileges" "lecture" {
  for_each    = { for l in local.lecture : "${l.role}.${l.schema}.${l.owner}" => l }
  database    = var.pg_database
  role        = each.value.role
  schema      = each.value.schema
  owner       = each.value.owner
  object_type = "table"
  privileges  = ["SELECT"]
  depends_on  = [postgresql_role.profils, postgresql_schema.zones]
}