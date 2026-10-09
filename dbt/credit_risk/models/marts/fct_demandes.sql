-- Grain : une demande de crédit en cours. Taux d'effort = annuité / revenu annuel.
select
    client_id,
    origine,
    type_contrat,
    montant_credit,
    annuite,
    revenu_annuel,
    prix_bien,
    round(annuite / nullif(revenu_annuel, 0), 4) as taux_effort,
    defaut_observe          -- variable TARGET : différente du défaut à 90 jours (H6)
from {{ ref('stg_homecredit__demandes') }}