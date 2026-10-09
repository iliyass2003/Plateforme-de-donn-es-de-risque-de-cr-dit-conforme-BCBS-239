-- Un lot doit pouvoir passer de EN_COURS à SUCCES ou ECHEC.
-- Seules ces 3 colonnes de batch_log sont modifiables ; aucune suppression possible.
GRANT UPDATE (statut, fin, message) ON ctl.batch_log TO role_ingestion, role_transformation;