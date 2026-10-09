-- Une ligne par client. Âge calculé à T0 (H1). Le sexe sera masqué au Lot 8 (P11).
select
    client_id,
    origine,
    sexe,
    nb_enfants,
    revenu_annuel,
    case
        when revenu_annuel < 100000 then '1. Moins de 100k'
        when revenu_annuel < 200000 then '2. 100k-200k'
        when revenu_annuel < 300000 then '3. 200k-300k'
        else '4. 300k et plus'
    end                                                         as tranche_revenu,
    extract(year from age(date '{{ var("t0_date") }}', date_naissance))::int as age,
    case
        when age(date '{{ var("t0_date") }}', date_naissance) < interval '25 years' then '1. Moins de 25 ans'
        when age(date '{{ var("t0_date") }}', date_naissance) < interval '35 years' then '2. 25-34 ans'
        when age(date '{{ var("t0_date") }}', date_naissance) < interval '45 years' then '3. 35-44 ans'
        when age(date '{{ var("t0_date") }}', date_naissance) < interval '55 years' then '4. 45-54 ans'
        else '5. 55 ans et plus'
    end                                                         as tranche_age,
    type_revenu,
    niveau_etudes,
    situation_familiale,
    profession,
    est_sans_emploi,
    note_region
from {{ ref('stg_homecredit__demandes') }}