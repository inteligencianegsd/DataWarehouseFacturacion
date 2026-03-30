{{ config(
    materialized='table',
    alias='camunda_operatividad'
) }}

WITH cleaned_articulos AS (
    SELECT
        TRIM(UPPER(cedula)) as cedula,
        COALESCE(fecha_aprobacion, fecha_inicio_tramite) as fecha_aprobacion,
        TRIM(UPPER(factura)) as numero_factura,
        TRIM(UPPER(ruc)) as ruc,
        TRIM(UPPER(tipo_firma)) as tipo_firma,
        TRIM(UPPER(serial_firma)) as serial_firma,
        fecha_inicio_tramite,
        TRIM(UPPER(ruc_aux)) as ruc_aux,
        CASE
            WHEN TRIM(UPPER(medio)) = 'TOKEN' THEN 'TOKEN'
            ELSE 'ARCHIVO'
        END as medio,
        sf_control,
        CASE
            WHEN TRIM(UPPER(producto)) IN ('EMISION SF SIN FIRMA', 'SF SIN FIRMA') THEN 'SF SIN FIRMA'
            WHEN TRIM(UPPER(producto)) IN ('RENOVACION SF', 'EMISION SF')          THEN 'SF CON FIRMA'
            WHEN TRIM(UPPER(producto)) IN ('EMISION', 'RENOVACION')                THEN 'FIRMA'
            ELSE TRIM(UPPER(producto))
        END as producto,
        TRIM(UPPER(grupo_vendedor)) AS grupo_vendedor
    FROM {{ source("camunda_bronze", "camunda_operatividad") }}
),

enriched AS (
    SELECT
        *,
        CASE
            -- FIRMA: agrupar por cedula, ruc_aux, tipo_firma
            WHEN producto = 'FIRMA' AND fecha_aprobacion = MIN(fecha_aprobacion) OVER (
                PARTITION BY cedula
                ORDER BY fecha_aprobacion
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) THEN 'NUEVO'

            -- SF CON FIRMA y SF SIN FIRMA: agrupar solo por ruc_aux
            WHEN producto IN ('SF CON FIRMA', 'SF SIN FIRMA') AND fecha_aprobacion = MIN(fecha_aprobacion) OVER (
                PARTITION BY ruc_aux
                ORDER BY fecha_aprobacion
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) THEN 'NUEVO'

            ELSE 'RENOVACION'
        END as tipo_emision
    FROM cleaned_articulos
)

SELECT * FROM enriched