{{ config(
    materialized='table',
    alias='fenix_rencon'
)}}
WITH cleaned_rencon AS (
    SELECT
        id_sec,
        TRIM(codcta) AS codigo_cuenta,
        importe,
        TRIM(codasi) AS codigo_asiento,
        fecasi AS fecha_asiento
    FROM {{ source("fenix_bronze", "fenix_rencon") }}
)

SELECT
    id_sec,
    codigo_cuenta,
    importe,
    codigo_asiento,
    fecha_asiento
FROM cleaned_rencon
