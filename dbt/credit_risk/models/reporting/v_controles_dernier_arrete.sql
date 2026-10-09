-- Résultats des contrôles du dernier lot de contrôle.
select controle_id, couche, gravite, statut, valeur, seuil, message
from {{ source('ctl', 'control_results') }}
where batch_id = (select max(batch_id) from {{ source('ctl', 'dq_score') }})