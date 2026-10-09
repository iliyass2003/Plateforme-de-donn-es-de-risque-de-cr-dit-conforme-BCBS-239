{# Hypothèse H1 : convertit un nombre de jours relatif à la demande en date réelle (T0 + jours). #}
{% macro jours_vers_date(colonne) -%}
    (date '{{ var("t0_date") }}' + cast(cast({{ colonne }} as numeric) as integer))
{%- endmacro %}