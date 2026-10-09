-- Vue de reporting de fct_exposition_mensuelle (aucune donnée personnelle sensible).
select * from {{ ref('fct_exposition_mensuelle') }}
