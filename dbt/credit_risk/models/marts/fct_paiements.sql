-- Grain : un paiement d'une échéance (H11).
select
    paiement_id, contrat_id, client_id, arrete,
    numero_echeance, date_prevue, date_paiement,
    montant_du, montant_paye, reste_du_echeance,
    jours_retard_paiement, paye_en_retard, non_paye, contrat_connu
from {{ ref('int_paiements_enrichis') }}