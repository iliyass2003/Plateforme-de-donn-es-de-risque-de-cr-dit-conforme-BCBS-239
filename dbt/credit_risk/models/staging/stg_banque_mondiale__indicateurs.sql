-- Indicateurs macroéconomiques du Maroc, typés (hypothèse H4)
select
    indicateur_code,
    indicateur_nom,
    pays                        as code_pays,
    cast(annee as integer)      as annee,
    cast(valeur as numeric)     as valeur,
    _batch_id,
    _source_file
from {{ source('bronze', 'banque_mondiale') }}
where valeur is not null
  and indicateur_code <> 'FR.INR.LEND'   -- retiré, indisponible pour le Maroc (note H4)