-- Les tranches de retard, issues du référentiel (seed) : modifiables sans toucher au code (P6).
select tranche_code, tranche_libelle, jours_min, jours_max
from {{ ref('ref_tranches_retard') }}