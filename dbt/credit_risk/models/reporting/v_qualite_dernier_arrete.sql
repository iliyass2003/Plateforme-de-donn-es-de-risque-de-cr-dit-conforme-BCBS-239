-- Score qualité du dernier lot de contrôle publié, par dimension.
select q.dimension, q.score, b.batch_id, b.statut, b.fin as publie_le
from {{ source('ctl', 'dq_score') }} q
join {{ source('ctl', 'batch_log') }} b on b.batch_id = q.batch_id
where q.batch_id = (select max(batch_id) from {{ source('ctl', 'dq_score') }})