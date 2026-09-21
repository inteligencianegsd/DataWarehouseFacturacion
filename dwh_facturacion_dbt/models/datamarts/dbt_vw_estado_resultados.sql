{{ config(
    materialized='view',
    alias='vw_estado_resultados'
) }}

SELECT
    fecha,
    valor,
    cuenta
FROM {{ ref('dbt_fact_cuentas') }}
