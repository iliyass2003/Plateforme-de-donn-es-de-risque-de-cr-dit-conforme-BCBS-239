-- Grain : un crédit du client dans un autre établissement (H3, H12).
select
    credit_externe_id, client_id, statut_credit, type_credit,
    devise, est_devise_principale, date_ouverture,
    montant_credit, dette_restante, montant_en_retard, jours_retard, est_trop_percu
from {{ ref('stg_homecredit__credits_externes') }}