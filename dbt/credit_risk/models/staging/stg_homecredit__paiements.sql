-- Paiements des échéances. H11 : grain = un paiement ; une échéance peut avoir
-- plusieurs lignes, d'où une clé technique construite sur l'empreinte de la ligne.
select
    _row_hash || '-' || row_number() over (partition by _row_hash order by _loaded_at) as paiement_id,
    cast(sk_id_prev as bigint)                              as contrat_id,
    cast(sk_id_curr as bigint)                              as client_id,
    cast(cast(num_instalment_version as numeric) as integer) as version_calendrier,
    cast(cast(num_instalment_number as numeric) as integer)  as numero_echeance,
    {{ jours_vers_date('days_instalment') }}                as date_prevue,
    {{ jours_vers_date('days_entry_payment') }}             as date_paiement,
    cast(amt_instalment as numeric(18, 2))                  as montant_du,
    cast(amt_payment as numeric(18, 2))                     as montant_paye,
    _arrete                                                 as arrete,
    _batch_id,
    _source_file
from {{ source('bronze', 'installments_payments') }}