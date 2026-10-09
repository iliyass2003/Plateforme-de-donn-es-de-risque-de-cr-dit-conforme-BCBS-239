-- Suivi mensuel des prêts point de vente et cash.
-- H6 : le défaut se mesure sur le retard significatif (sk_dpd_def).
select
    cast(sk_id_prev as bigint) || '-' || _arrete            as cle,
    cast(sk_id_prev as bigint)                              as contrat_id,
    cast(sk_id_curr as bigint)                              as client_id,
    _arrete                                                 as arrete,
    cast(cast(cnt_instalment as numeric) as integer)        as nb_echeances_total,
    cast(cast(cnt_instalment_future as numeric) as integer) as nb_echeances_restantes,
    name_contract_status                                    as statut_contrat,
    cast(sk_dpd as integer)                                 as jours_retard_brut,
    cast(sk_dpd_def as integer)                             as jours_retard_significatif,
    _batch_id,
    _source_file
from {{ source('bronze', 'pos_cash_balance') }}