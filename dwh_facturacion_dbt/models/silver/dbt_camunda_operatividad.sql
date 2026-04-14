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
            WHEN TRIM(UPPER(producto)) IN ('EMISION SF SIN FIRMA', 'SF SIN FIRMA', 'SF CON FIRMA') THEN 'SF'
            WHEN TRIM(UPPER(producto)) IN ('RENOVACION SF', 'EMISION SF')          THEN 'SF'
            WHEN TRIM(UPPER(producto)) IN ('EMISION', 'RENOVACION')                THEN 'FIRMA'
            ELSE TRIM(UPPER(producto))
        END as producto,
        TRIM(UPPER(grupo_vendedor)) AS grupo_vendedor,
        estado,
        fecha_factura
    FROM {{ source("camunda_bronze", "camunda_operatividad") }}
    -- Ya no filtramos por estado, traemos todo
),

con_fecha_primer_aprobado AS (
    SELECT
        *,
        CASE
            WHEN producto = 'FIRMA' THEN
                MIN(CASE WHEN estado = 'APROBADO' THEN fecha_aprobacion END)
                    OVER (PARTITION BY cedula, producto)
            WHEN producto = 'SF' THEN
                MIN(CASE WHEN estado = 'APROBADO' THEN fecha_aprobacion END)
                    OVER (PARTITION BY ruc_aux, producto)
        END as fecha_primer_aprobado_con_producto,

        CASE
            WHEN producto = 'FIRMA' THEN
                MIN(CASE WHEN estado = 'APROBADO' THEN fecha_aprobacion END)
                    OVER (PARTITION BY cedula)
            WHEN producto = 'SF' THEN
                MIN(CASE WHEN estado = 'APROBADO' THEN fecha_aprobacion END)
                    OVER (PARTITION BY ruc_aux)
        END as fecha_primer_aprobado_sin_producto
    FROM cleaned_articulos
),

-- Luego en el siguiente CTE seleccionas cuál usar:
enriched_fecha_primera_aprobacion AS (
    SELECT
        *,
        CASE
            WHEN fecha_aprobacion >= '2026-04-09' THEN fecha_primer_aprobado_con_producto
            ELSE fecha_primer_aprobado_sin_producto
        END as fecha_primer_aprobado
    FROM con_fecha_primer_aprobado
),

enriched AS (
    SELECT
        *,
        CASE
            -- Registros APROVADOS: el más antiguo es NUEVO
            WHEN estado = 'APROBADO'
                 AND fecha_aprobacion = fecha_primer_aprobado
                THEN 'NUEVO'

            -- Registros NO aprobados: si su fecha_factura es anterior
            -- a la primera aprobación del grupo, es NUEVO
            WHEN estado != 'APROBADO'
                 AND fecha_factura < fecha_primer_aprobado
                THEN 'NUEVO'

            ELSE 'RENOVACION'
        END as tipo_venta
    FROM enriched_fecha_primera_aprobacion
),


filter_register AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY serial_firma
            ORDER BY
                CASE WHEN estado = 'APROBADO' THEN 1 ELSE 2 END,
                fecha_aprobacion DESC
        ) as rn
    FROM enriched
)

SELECT
    cedula,
    fecha_aprobacion,
    numero_factura,
    ruc,
    tipo_firma,
    serial_firma,
    fecha_inicio_tramite,
    ruc_aux,
    medio,
    sf_control,
    producto,
    grupo_vendedor,
    estado,
    fecha_factura,
    fecha_primer_aprobado,
    tipo_venta
FROM filter_register
WHERE rn = 1