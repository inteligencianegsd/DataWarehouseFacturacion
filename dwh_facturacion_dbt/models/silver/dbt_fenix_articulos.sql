{{ config(
    materialized='table',
    alias='fenix_articulos'
) }}

WITH cleaned_articulos AS (

    SELECT
        creation_date,
        update_date,
        TRIM(codart) AS codigo,
        REPLACE(TRIM(UPPER(nomart)), 'ANIO', 'ANO') AS nombre,
        NULLIF(TRIM(UPPER(nomart2)), '') AS aux_familia
    FROM {{ source("fenix_bronze", "fenix_articulos") }}

),

parsed_articulos AS (

    SELECT
        creation_date,
        update_date,
        codigo,
        nombre,
        aux_familia,

        SUBSTRING(nombre FROM '([0-9]+\s+(MES|MESES|ANO|ANOS|SEMANA|SEMANAS))') AS vigencia,

        SUBSTRING(
            nombre
            FROM '([0-9]+\s+TRANSACC|PLAN\s+ILIMITADO)'
        ) AS aux_tipo_plan

    FROM cleaned_articulos

),

enriched_articulos AS (

    SELECT
        creation_date,
        update_date,
        codigo,
        nombre,
        vigencia,

        CASE
            WHEN nombre LIKE 'UPGRADE%' THEN 'UPGRADE'
            WHEN nombre LIKE 'PUNTO DE EMISION%' THEN 'PUNTO DE EMISION'
            WHEN nombre LIKE '%FIRMA ELEC%' AND vigencia IS NOT NULL THEN 'FIRMAS ELECTRONICAS'
            WHEN aux_tipo_plan IS NOT NULL AND nombre LIKE '%FACT%' THEN 'SISTEMA DE FACTURACION'
            ELSE aux_familia
        END AS familia,

        CASE
            WHEN aux_tipo_plan = '25 TRANSACC' THEN 'PLAN MINI'
            WHEN aux_tipo_plan = '75 TRANSACC' THEN 'PLAN BASICO'
            WHEN aux_tipo_plan = '150 TRANSACC' THEN 'PLAN ESENCIAL'
            WHEN aux_tipo_plan = '350 TRANSACC' THEN 'PLAN ESTANDAR'
            WHEN aux_tipo_plan = 'PLAN ILIMITADO' THEN 'PLAN PREMIUM'
            WHEN aux_tipo_plan LIKE '%TRANSACC' THEN CONCAT('PLAN ', aux_tipo_plan)
            ELSE aux_tipo_plan
        END AS tipo_plan

    FROM parsed_articulos

)

SELECT
    COALESCE(fac.creation_date, enr.creation_date) AS creation_date,
    COALESCE(fac.update_date, enr.update_date) AS update_date,
    COALESCE(TRIM(fac.codigo), enr.codigo) AS codigo,
    COALESCE(TRIM(fac.nombre), enr.nombre) AS nombre,
    COALESCE(TRIM(fac.vigencia), enr.vigencia) AS vigencia,
    COALESCE(TRIM(fac.familia), enr.familia) AS familia,
    COALESCE(TRIM(fac.tipo_plan), enr.tipo_plan) AS tipo_plan,
    TRIM(fac.concepto) AS concepto

FROM enriched_articulos enr
FULL OUTER JOIN {{ ref('fenix_articulos_corregidos') }} fac ON enr.codigo = fac.codigo