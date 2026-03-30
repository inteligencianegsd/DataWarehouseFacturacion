{{ config(
    materialized='table',
    alias='fenix_clientes'
)}}
WITH cleaned_clientes AS (
    SELECT
        creation_date,
        update_date,
        TRIM(codcli) AS codigo,
        TRIM(UPPER(nomcli)) AS nombre,
        TRIM(cif) as cif,
        CASE WHEN cif IN ('0991327371001', '1792186927001', '1792496136001') THEN TRUE -- TELCONET, GK, SYSTOR
        ELSE FALSE END AS is_same_corporate_group
    FROM {{ source("fenix_bronze", "fenix_clientes") }}
)

-- 3. Consulta final
SELECT
    creation_date,
    update_date,
    codigo,
    nombre,
    cif,
    is_same_corporate_group
FROM cleaned_clientes