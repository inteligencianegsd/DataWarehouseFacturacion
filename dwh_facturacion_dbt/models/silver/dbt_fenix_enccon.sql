{{ config(
    materialized='table',
    alias='fenix_enccon'
)}}
WITH cleaned_enccon AS (
    SELECT
        id_codasi,
        TRIM(codasi) AS codigo_asiento,
        fecasi AS fecha_asiento
    FROM {{ source("fenix_bronze", "fenix_enccon") }}
)

SELECT
    id_codasi,
    codigo_asiento,
    fecha_asiento
FROM cleaned_enccon
