-- Réconciliation source (manifestes de la landing) / cible (gold), par contrôle et par arrêté.
-- BCBS 239 : P3 (exactitude) et P4 (exhaustivité).

with manifeste as (
    -- dernière version de chaque fichier reçu
    select distinct on (chemin_objet) table_name, arrete, nb_lignes, sommes
    from {{ source('ctl', 'file_manifest') }}
    where source <> 'banque_mondiale'
    order by chemin_objet, id desc
),

controles as (

    select 'RC-01' as controle_id, max(m.arrete) as arrete,
           'Nombre de demandes (train + test)' as indicateur,
           sum(m.nb_lignes)::numeric as valeur_source,
           (select count(*) from {{ ref('fct_demandes') }})::numeric as valeur_cible,
           0::numeric as tolerance
    from manifeste m
    where m.table_name in ('application_train', 'application_test')

    union all
    select 'RC-02', max(m.arrete), 'Somme des montants de crédit demandés',
           sum((m.sommes ->> 'AMT_CREDIT')::numeric),
           (select sum(montant_credit) from {{ ref('fct_demandes') }}),
           0.0001
    from manifeste m
    where m.table_name in ('application_train', 'application_test')

    union all
    select 'RC-03', m.arrete, 'Somme des soldes de cartes',
           (m.sommes ->> 'AMT_BALANCE')::numeric,
           coalesce((select sum(f.encours) from {{ ref('fct_exposition_mensuelle') }} f
                     where f.type_suivi = 'carte' and f.arrete = m.arrete), 0),
           0.0001
    from manifeste m
    where m.table_name = 'credit_card_balance'

    union all
    select 'RC-04', m.arrete, 'Somme des montants payés',
           (m.sommes ->> 'AMT_PAYMENT')::numeric,
           coalesce((select sum(p.montant_paye) from {{ ref('fct_paiements') }} p
                     where p.arrete = m.arrete), 0),
           0.0001
    from manifeste m
    where m.table_name = 'installments_payments'

    union all
    select 'RC-05', s.arrete, 'Encours : fait des expositions / synthèse',
           (select sum(f.encours) from {{ ref('fct_exposition_mensuelle') }} f
            where f.est_en_portefeuille and f.arrete = s.arrete),
           s.encours_total,
           0
    from {{ ref('agg_synthese_arrete') }} s

    union all
    select 'RC-06', m.arrete, 'Lignes de suivi des prêts',
           m.nb_lignes::numeric,
           (select count(*) from {{ ref('fct_exposition_mensuelle') }} f
            where f.type_suivi = 'pret' and f.arrete = m.arrete)::numeric,
           0
    from manifeste m
    where m.table_name = 'pos_cash_balance'
)

select
    controle_id || '-' || arrete                                    as cle,
    controle_id,
    arrete,
    indicateur,
    valeur_source,
    valeur_cible,
    abs(valeur_source - valeur_cible) / nullif(abs(valeur_source), 0) as ecart_relatif,
    tolerance,
    case
        when coalesce(abs(valeur_source - valeur_cible) / nullif(abs(valeur_source), 0), 0) <= tolerance
        then 'OK' else 'KO'
    end                                                             as statut
from controles