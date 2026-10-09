-- Suivi mensuel des cartes de crédit. H6 : retard significatif = sk_dpd_def.
select
    cast(sk_id_prev as bigint) || '-' || _arrete        as cle,
    cast(sk_id_prev as bigint)                          as contrat_id,
    cast(sk_id_curr as bigint)                          as client_id,
    _arrete                                             as arrete,
    cast(amt_balance as numeric(18, 2))                 as solde,
    cast(amt_credit_limit_actual as numeric(18, 2))     as plafond,
    cast(amt_receivable_principal as numeric(18, 2))    as capital_restant,
    cast(amt_payment_total_current as numeric(18, 2))   as montant_paye_mois,
    name_contract_status                                as statut_contrat,
    cast(sk_dpd as integer)                             as jours_retard_brut,
    cast(sk_dpd_def as integer)                         as jours_retard_significatif,
    _batch_id,
    _source_file
from {{ source('bronze', 'credit_card_balance') }}