-- Crédits du client dans d'autres établissements (bureau de crédit).
-- H3 : seule la devise principale sera agrégée ; les autres sont signalées.
select
    cast(sk_id_bureau as bigint)                    as credit_externe_id,
    cast(sk_id_curr as bigint)                      as client_id,
    credit_active                                   as statut_credit,
    credit_type                                     as type_credit,
    credit_currency                                 as devise,
    (credit_currency = 'currency 1')                as est_devise_principale,
    {{ jours_vers_date('days_credit') }}            as date_ouverture,
    cast(credit_day_overdue as integer)             as jours_retard,
    cast(amt_credit_sum as numeric(18, 2))          as montant_credit,
    cast(amt_credit_sum_debt as numeric(18, 2))     as dette_restante,
    cast(amt_credit_sum_overdue as numeric(18, 2))  as montant_en_retard,
    _arrete,
    _batch_id,
    _source_file
from {{ source('bronze', 'bureau') }}