{{ config(
    materialized='view',
    alias='estado_resultados'
) }}

SELECT
    fecha,
    valor,
    cuenta
FROM {{ ref('dbt_fact_estado_resultados') }}
