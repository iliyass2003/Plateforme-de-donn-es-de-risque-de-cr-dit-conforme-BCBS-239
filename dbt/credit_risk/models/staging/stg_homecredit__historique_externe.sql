-- Statut mensuel des crédits externes : 0 = à jour, 1 à 5 = tranches de retard,
-- C = clôturé, X = inconnu. Les orphelins (H11) seront exclus en intermediate.
select
    cast(sk_id_bureau as bigint) || '-' || _arrete  as cle,
    cast(sk_id_bureau as bigint)                    as credit_externe_id,
    _arrete                                         as arrete,
    status                                          as statut_mois,
    _batch_id,
    _source_file
from {{ source('bronze', 'bureau_balance') }}