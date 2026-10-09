-- Paiements avec retard et écart dû / payé.
-- H11 : une échéance peut avoir plusieurs paiements ; l'écart se mesure par échéance.
with paiements as (
    select p.*
    from {{ ref('stg_homecredit__paiements') }} p
    where p.paiement_id not in (select cle from {{ ref('int_quarantaine') }} where entite = 'paiements')
)

select
    p.paiement_id,
    p.contrat_id,
    p.client_id,
    p.arrete,
    p.version_calendrier,
    p.numero_echeance,
    p.date_prevue,
    p.date_paiement,
    p.montant_du,
    p.montant_paye,
    (p.date_paiement is null)                                   as non_paye,
    greatest(p.date_paiement - p.date_prevue, 0)                as jours_retard_paiement,
    (p.date_paiement > p.date_prevue)                           as paye_en_retard,
    sum(p.montant_paye) over (
        partition by p.contrat_id, p.version_calendrier, p.numero_echeance
    )                                                           as total_paye_echeance,
    p.montant_du - sum(p.montant_paye) over (
        partition by p.contrat_id, p.version_calendrier, p.numero_echeance
    )                                                           as reste_du_echeance,
    (c.contrat_id is not null)                                  as contrat_connu
from paiements p
left join {{ ref('int_contrats') }} c on c.contrat_id = p.contrat_id