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
        total,
        total_iva,
        CASE
            WHEN TRIM(codven) IN ('0', '28', '123',  'NO') THEN '1001'
            ELSE TRIM(codven) END
        AS codigo_vendedor,
        emision::date AS fecha_emision,
        CASE WHEN TRIM(numfac) LIKE 'DV%' THEN TRUE ELSE FALSE END AS is_nc

    FROM {{ source("fenix_bronze", "fenix_facturas") }}
    WHERE total_iva <> 0

),

fenix_dedup AS (
    SELECT
        codigo_documento,
        MAX(co_0.grupo_vendedor) AS grupo_vendedor_temp
    FROM cleaned_facturas cf_0
    JOIN camunda_dedup co_0 ON cf_0.numero_factura = co_0.numero_factura
    WHERE NOT is_nc
    GROUP BY codigo_documento
),




parsed_facturas AS (

    SELECT
        cf_0.codigo_factura,
        CASE
            WHEN cf_0.codigo_documento = '' THEN cf_0.codigo_factura
            ELSE cf_0.codigo_documento
        END AS codigo_documento,
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
        cf_0.total,
        cf_0.total_iva,
        cf_0.codigo_vendedor,
        cf_0.fecha_emision,

        COALESCE(
            NULLIF(
                split_part(
                    split_part(cf_0.comentario_2, 'CODDESCUENTO ', 2),
                    ' ',
                    1
                ),
                ''
            ),
            'SIN CODIGO DE DESCUENTO'
        ) AS codigo_descuento,

        fo_0.grupo_vendedor_temp,
        cf_0.is_nc

    FROM cleaned_facturas cf_0
    LEFT JOIN fenix_dedup fo_0 ON cf_0.codigo_documento = fo_0.codigo_documento

),

facturas_convenios AS (
    SELECT fc_0.codigo_documento
    FROM parsed_facturas fc_0
    WHERE
        fc_0.codigo_descuento LIKE '%ALIANZA%'
        OR fc_0.codigo_descuento LIKE '%COLEGIOABOGADO%'
        OR fc_0.codigo_descuento LIKE '%ANAMER%'
        OR fc_0.codigo_descuento LIKE '%FEUE%'

),

facturas_sucursales AS (
    SELECT
        pf.codigo_documento,
        COALESCE(rit_0.id_sucursal, pe.id_sucursal) AS id_sucursal,
        pf.codigo_vendedor


    FROM parsed_facturas pf
    JOIN {{ source("features", "puntos_emision") }} pe
        ON pe.serial_punto_emision = pf.numero_serie
        AND pf.fecha_emision >= pe.fecha_apertura
        AND pf.fecha_emision < pe.fecha_cierre
    LEFT JOIN {{ref('reasignacion_islas_temporales')}} rit_0 ON pf.numero_factura = rit_0.numero_factura
    WHERE NOT pf.is_nc

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
            WHEN (dco_0.codigo IS NOT NULL AND fc_0.codigo_documento IS NOT NULL) THEN REGEXP_REPLACE(pf.comentario_3, '^([^.]+)\.[^.]+', '\1.CN')
            ELSE pf.comentario_3
        END AS comentario_3,


        pf.codigo_descuento,

        pf.subtotal,
        pf.valor_descuento,
        pf.total,
        pf.total_iva,
        CASE
            WHEN fs_0.codigo_vendedor IS NOT NULL THEN fs_0.codigo_vendedor
            ELSE pf.codigo_vendedor
        END AS codigo_vendedor,
        pf.fecha_emision,
        grupo_vendedor_temp,
        CASE
            WHEN fs_0.id_sucursal IS NOT NULL THEN fs_0.id_sucursal
            ELSE pe.id_sucursal
        END AS id_sucursal,
        pf.is_nc


    FROM parsed_facturas pf
    LEFT JOIN facturas_sucursales fs_0 ON pf.codigo_documento = fs_0.codigo_documento
    LEFT JOIN {{ source("features", "puntos_emision") }} pe
        ON pe.serial_punto_emision = pf.numero_serie
        AND pf.fecha_emision >= pe.fecha_apertura
        AND pf.fecha_emision < pe.fecha_cierre
    LEFT JOIN {{ref('dbt_fenix_codigos')}} dco_0 ON pf.comentario_3 = dco_0.codigo
    LEFT JOIN facturas_convenios fc_0 ON pf.codigo_documento = fc_0.codigo_documento
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
    total,
    total_iva,
    codigo_vendedor,
    fecha_emision,
    id_sucursal,
    grupo_vendedor_temp,
    is_nc
FROM enriched_facturas