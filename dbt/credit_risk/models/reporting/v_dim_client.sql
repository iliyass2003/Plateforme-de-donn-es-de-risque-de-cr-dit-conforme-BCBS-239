-- Dimension client pour Power BI, minimisée (loi 09-08, BCBS 239 P11) :
-- ni sexe, ni âge exact, ni revenu exact ; seulement des tranches.
select
    client_id,
    origine,
    tranche_age,
    tranche_revenu,
    type_revenu,
    niveau_etudes,
    situation_familiale,
    est_sans_emploi,
    note_region
from {{ ref('dim_client') }}