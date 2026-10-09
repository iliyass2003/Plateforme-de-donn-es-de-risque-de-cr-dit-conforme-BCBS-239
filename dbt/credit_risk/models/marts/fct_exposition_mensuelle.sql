-- Grain : un contrat × un arrêté. Incrémental : seuls le dernier arrêté et les nouveaux sont retraités.
{{ config(
    materialized = 'incremental',
    unique_key = 'arrete',
    incremental_strategy = 'delete+insert'
) }}

select
    e.cle,
    a.arrete_key,
    e.arrete,
    e.contrat_id,
    e.client_id,
    e.tranche_code,
    e.type_suivi,
    e.segment,
    e.statut_contrat,
    e.encours,
    e.plafond,
    e.jours_retard_brut,
    e.jours_retard_significatif,
    e.est_defaut,
    e.est_en_portefeuille,
    e.contrat_connu,
    e.encours_connu,
    e.encours_reporte
from {{ ref('int_expositions_mensuelles') }} e
join {{ ref('dim_arrete') }} a on a.arrete = e.arrete

{% if is_incremental() %}
where e.arrete >= (select max(arrete) from {{ this }})
{% endif %}