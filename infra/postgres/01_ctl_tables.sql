-- Tables de contrôle : piste d'audit de la plateforme (BCBS 239)
-- Rejouable sans risque grâce à IF NOT EXISTS

CREATE TABLE IF NOT EXISTS ctl.batch_log (
    batch_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    arrete       DATE        NOT NULL,
    statut       TEXT        NOT NULL CHECK (statut IN ('EN_COURS', 'SUCCES', 'ECHEC', 'PUBLIE')),
    debut        TIMESTAMPTZ NOT NULL DEFAULT now(),
    fin          TIMESTAMPTZ,
    message      TEXT
);

CREATE TABLE IF NOT EXISTS ctl.file_manifest (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id     BIGINT      NOT NULL REFERENCES ctl.batch_log (batch_id),
    source       TEXT        NOT NULL,
    table_name   TEXT        NOT NULL,
    arrete       DATE        NOT NULL,
    chemin_objet TEXT        NOT NULL,
    nb_lignes    BIGINT      NOT NULL,
    sha256       CHAR(64)    NOT NULL,
    sommes       JSONB,
    recu_le      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ctl.control_results (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id     BIGINT      NOT NULL REFERENCES ctl.batch_log (batch_id),
    controle_id  TEXT        NOT NULL,
    couche       TEXT        NOT NULL,
    gravite      TEXT        NOT NULL CHECK (gravite IN ('BLOQUANT', 'AVERTISSEMENT')),
    statut       TEXT        NOT NULL CHECK (statut IN ('OK', 'KO')),
    valeur       NUMERIC,
    seuil        NUMERIC,
    message      TEXT,
    execute_le   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ctl.reconciliation (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id       BIGINT      NOT NULL REFERENCES ctl.batch_log (batch_id),
    controle_id    TEXT        NOT NULL,
    indicateur     TEXT        NOT NULL,
    valeur_source  NUMERIC     NOT NULL,
    valeur_cible   NUMERIC     NOT NULL,
    ecart_relatif  NUMERIC,
    tolerance      NUMERIC     NOT NULL,
    statut         TEXT        NOT NULL CHECK (statut IN ('OK', 'KO')),
    execute_le     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ctl.dq_score (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id     BIGINT       NOT NULL REFERENCES ctl.batch_log (batch_id),
    arrete       DATE         NOT NULL,
    dimension    TEXT         NOT NULL CHECK (dimension IN ('exactitude', 'completude', 'actualite', 'coherence', 'global')),
    score        NUMERIC(5,2) NOT NULL,
    calcule_le   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Ajout seul : insérer et lire, jamais modifier ni supprimer
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA ctl TO role_ingestion, role_transformation;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ctl TO role_ingestion, role_transformation;
GRANT SELECT ON ALL TABLES IN SCHEMA ctl TO role_auditeur;