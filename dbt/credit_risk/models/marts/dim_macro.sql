-- Une ligne par année : indicateurs macroéconomiques du Maroc (H4).
select
    annee,
    max(valeur) filter (where indicateur_code = 'NY.GDP.MKTP.KD.ZG') as croissance_pib_reel,
    max(valeur) filter (where indicateur_code = 'FP.CPI.TOTL.ZG')    as inflation,
    max(valeur) filter (where indicateur_code = 'SL.UEM.TOTL.ZS')    as chomage
from {{ ref('stg_banque_mondiale__indicateurs') }}
group by annee