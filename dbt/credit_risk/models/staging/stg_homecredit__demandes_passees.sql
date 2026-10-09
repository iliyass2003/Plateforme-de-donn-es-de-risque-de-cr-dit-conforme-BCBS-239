-- Demandes passées chez la banque. Toutes les lignes sont gardées ;
-- H9 est préparée par des indicateurs, le filtre se fera en intermediate.
select
    cast(sk_id_prev as bigint)                      as contrat_id,
    cast(sk_id_curr as bigint)                      as client_id,
    name_contract_type                              as type_produit,
    nullif(name_portfolio, 'XNA')                   as portefeuille,
    name_contract_status                            as statut_demande,
    cast(amt_application as numeric(18, 2))         as montant_demande,
    cast(amt_credit as numeric(18, 2))              as montant_accorde,
    cast(amt_annuity as numeric(18, 2))             as mensualite,
    cast(cast(cnt_payment as numeric) as integer)   as nb_echeances,
    {{ jours_vers_date('days_decision') }}          as date_decision,
    (name_contract_status = 'Approved')             as est_contrat,
    (flag_last_appl_per_contract = 'Y'
     and nflag_last_appl_in_day = '1')              as est_derniere_demande,
    _arrete,
    _batch_id,
    _source_file
from {{ source('bronze', 'previous_application') }}