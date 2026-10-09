-- Vue de reporting de dim_contrat (aucune donnée personnelle sensible).
select * from {{ ref('dim_contrat') }}
