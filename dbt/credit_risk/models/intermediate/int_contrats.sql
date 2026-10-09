-- Contrats valides : demandes approuvées, dernière version, hors quarantaine (H9).
select
    contrat_id,
    client_id,
    case type_produit
        when 'Cash loans'      then 'Prêt cash'
        when 'Consumer loans'  then 'Point de vente'
        when 'Revolving loans' then 'Carte renouvelable'
        else 'Non renseigné'
    end                 as segment,
    montant_accorde,
    mensualite,
    nb_echeances,
    date_decision
from {{ ref('stg_homecredit__demandes_passees') }}
where est_contrat
  and est_derniere_demande
  and cast(contrat_id as text) not in (
      select cle from {{ ref('int_quarantaine') }} where entite = 'demandes_passees')