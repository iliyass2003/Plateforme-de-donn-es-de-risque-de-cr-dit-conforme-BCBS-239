-- Lignes invalides mises de côté avec leur motif (BCBS 239, P4 : rien ne disparaît).
-- Les modèles intermédiaires excluent ces lignes de leurs calculs.

select 'demandes' as entite, cast(client_id as text) as cle,
       'revenu nul ou négatif' as motif, _source_file
from {{ ref('stg_homecredit__demandes') }} where revenu_annuel <= 0

union all
select 'demandes', cast(client_id as text), 'montant de crédit nul ou négatif', _source_file
from {{ ref('stg_homecredit__demandes') }} where montant_credit <= 0

union all
select 'demandes_passees', cast(contrat_id as text), 'montant accordé négatif', _source_file
from {{ ref('stg_homecredit__demandes_passees') }} where montant_accorde < 0

union all
select 'suivi_prets', cle, 'échéances restantes négatives', _source_file
from {{ ref('stg_homecredit__suivi_prets') }} where nb_echeances_restantes < 0

union all
select 'suivi_prets', cle, 'retard négatif', _source_file
from {{ ref('stg_homecredit__suivi_prets') }} where jours_retard_brut < 0 or jours_retard_significatif < 0

union all
select 'suivi_cartes', cle, 'plafond négatif', _source_file
from {{ ref('stg_homecredit__suivi_cartes') }} where plafond < 0

union all
select 'paiements', paiement_id, 'montant dû ou payé négatif', _source_file
from {{ ref('stg_homecredit__paiements') }} where montant_du < 0 or montant_paye < 0

union all
select 'credits_externes', cast(credit_externe_id as text), 'montant de crédit négatif', _source_file
from {{ ref('stg_homecredit__credits_externes') }} where montant_credit < 0   -- une dette négative est un trop-perçu valide (H12)