{# Utilise exactement le schéma demandé (staging, intermediate, marts),
   au lieu du comportement par défaut de dbt qui l'aurait préfixé. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}{{ target.schema }}{%- else -%}{{ custom_schema_name | trim }}{%- endif -%}
{%- endmacro %}