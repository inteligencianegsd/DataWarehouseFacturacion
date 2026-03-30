{{ config(
    materialized='table',
    alias='fenix_facturas'
) }}

WITH camunda_dedup AS (
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY numero_factura
                ORDER BY fecha_aprobacion ASC
            ) as rn
        FROM {{ ref('dbt_camunda_operatividad') }}
    ) ranked
    WHERE rn = 1
),

cleaned_facturas AS (

    SELECT
        TRIM(numfac) AS codigo_factura,
        TRIM(numdoc) AS codigo_documento,
        TRIM(cliente) AS codigo_cliente,
        CONCAT(numser, pedido) AS numero_factura,

        TRIM(numser) AS numero_serie,

        UPPER(TRIM(comen1)) AS comentario_1,
        UPPER(TRIM(comen2)) AS comentario_2,
        UPPER(TRIM(comen3)) AS comentario_3,

        subtotal,
        desc0 AS valor_descuento,
        iva,
        total,
        total_iva,
        CASE
            WHEN TRIM(codven) IN ('0', '28', '123',  'NO') THEN '1001'
            ELSE TRIM(codven) END
        AS codigo_vendedor,
        emision::date AS fecha_emision

    FROM {{ source("fenix_bronze", "fenix_facturas") }}
    WHERE total_iva <> 0

),

parsed_facturas AS (

    SELECT
        cf_0.codigo_factura,
        cf_0.codigo_documento,
        cf_0.codigo_cliente,
        cf_0.numero_factura,
        cf_0.numero_serie,
        cf_0.comentario_1,
        cf_0.comentario_2,
        CASE
            WHEN cf_0.comentario_3 LIKE 'COEMRCIAL%' OR cf_0.comentario_3 LIKE 'COMERCIAL%' THEN 'COMERCIAL'
            ELSE cf_0.comentario_3 END
        AS comentario_3,
        cf_0.subtotal,
        cf_0.valor_descuento,
        cf_0.iva,
        cf_0.total,
        cf_0.total_iva,
        cf_0.codigo_vendedor,
        cf_0.fecha_emision,

        split_part(
            split_part(cf_0.comentario_2, 'CODDESCUENTO ', 2),
            ' ',
            1
        ) AS codigo_descuento,

        co_0.grupo_vendedor as grupo_vendedor_temp

    FROM cleaned_facturas cf_0
    LEFT JOIN camunda_dedup co_0 ON cf_0.numero_factura = co_0.numero_factura

),

enriched_facturas AS (

    SELECT
        pf.codigo_factura,
        pf.codigo_documento,
        pf.codigo_cliente,
        pf.numero_factura,
        pf.numero_serie,

        pf.comentario_1,
        pf.comentario_2,
        CASE
            WHEN REGEXP_LIKE(comentario_3, '^ADICIONAL [0-9]+ COMPROBANTES$') THEN 'SF.CA.MANUAL'
            WHEN (dco_0.codigo IS NOT NULL AND pf.codigo_descuento LIKE '%ALIANZA%') THEN REGEXP_REPLACE(pf.comentario_3, '^([^.]+)\.[^.]+', '\1.CN')
            ELSE pf.comentario_3
        END AS comentario_3,


        pf.codigo_descuento,

        pf.subtotal,
        pf.valor_descuento,
        pf.iva,
        pf.total,
        pf.total_iva,

        pf.codigo_vendedor,
        pf.fecha_emision,
        CASE
            WHEN rit_0.numero_factura IS NOT NULL THEN rit_0.id_sucursal
            ELSE pe.id_sucursal
        END AS id_sucursal,
        grupo_vendedor_temp

    FROM parsed_facturas pf
    LEFT  JOIN {{ source("features", "puntos_emision") }} pe
        ON pe.serial_punto_emision = pf.numero_serie
        AND pf.fecha_emision >= pe.fecha_apertura
        AND pf.fecha_emision < pe.fecha_cierre
    LEFT JOIN {{ref('reasignacion_islas_temporales')}} rit_0 ON pf.numero_factura = rit_0.numero_factura
    LEFT JOIN {{ref('dbt_dim_codigos')}} dco_0 ON pf.comentario_3 = dco_0.codigo
)

SELECT
    codigo_factura,
    codigo_documento,
    codigo_cliente,
    numero_factura,
    numero_serie,
    comentario_1,
    comentario_2,
    comentario_3,
    codigo_descuento,
    subtotal,
    valor_descuento,
    iva,
    total,
    total_iva,
    codigo_vendedor,
    fecha_emision,
    id_sucursal,
    grupo_vendedor_temp
FROM enriched_facturas