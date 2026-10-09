-- Vue de reporting de dim_arrete (aucune donnée personnelle sensible).
select * from {{ ref('dim_arrete') }}
