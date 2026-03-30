{{ config(
    materialized='table',
    alias='fenix_vendedores'
)}}

WITH cleaned_facturas AS (
    SELECT
        creation_date,
        update_date,
        TRIM(codven) AS codigo,
        TRIM(UPPER(nomven)) AS nombre,
        fecha_act AS fecha_actualizacion

    FROM {{ source("fenix_bronze", "fenix_vendedores")}}
)

SELECT
    creation_date,
    update_date,
    codigo,
    nombre,
    fecha_actualizacion
FROM cleaned_facturas