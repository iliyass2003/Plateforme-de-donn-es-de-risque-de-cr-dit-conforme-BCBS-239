-- Demandes de crédit en cours : train (avec défaut observé) et test réunis.
-- H1 : dates relatives converties. H5 : 365243 = sans emploi ou retraité.
with demandes as (
    select sk_id_curr, name_contract_type, code_gender, cnt_children, amt_income_total, amt_credit, amt_annuity, amt_goods_price, name_income_type, name_education_type, name_family_status, occupation_type, region_rating_client, days_birth, days_employed, ext_source_1, ext_source_2, ext_source_3, _arrete, _batch_id, _source_file, target, 'train' as origine from {{ source('bronze', 'application_train') }}
    union all
    select sk_id_curr, name_contract_type, code_gender, cnt_children, amt_income_total, amt_credit, amt_annuity, amt_goods_price, name_income_type, name_education_type, name_family_status, occupation_type, region_rating_client, days_birth, days_employed, ext_source_1, ext_source_2, ext_source_3, _arrete, _batch_id, _source_file, null as target, 'test' as origine from {{ source('bronze', 'application_test') }}
)

select
    cast(sk_id_curr as bigint)                          as client_id,
    origine,
    cast(target as integer)                             as defaut_observe,
    name_contract_type                                  as type_contrat,
    nullif(code_gender, 'XNA')                          as sexe,
    cast(cnt_children as integer)                       as nb_enfants,
    cast(amt_income_total as numeric(18, 2))            as revenu_annuel,
    cast(amt_credit as numeric(18, 2))                  as montant_credit,
    cast(amt_annuity as numeric(18, 2))                 as annuite,
    cast(amt_goods_price as numeric(18, 2))             as prix_bien,
    name_income_type                                    as type_revenu,
    name_education_type                                 as niveau_etudes,
    name_family_status                                  as situation_familiale,
    occupation_type                                     as profession,
    cast(region_rating_client as integer)               as note_region,
    {{ jours_vers_date('days_birth') }}                 as date_naissance,
    case when days_employed = '365243' then null
         else {{ jours_vers_date('days_employed') }} end as date_embauche,
    (days_employed = '365243')                          as est_sans_emploi,
    cast(ext_source_1 as numeric)                       as score_externe_1,
    cast(ext_source_2 as numeric)                       as score_externe_2,
    cast(ext_source_3 as numeric)                       as score_externe_3,
    _arrete,
    _batch_id,
    _source_file
from demandes