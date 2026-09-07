{{ config(
    materialized='table',
    alias='dim_facturas',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_facturas_id_factura_seq",
        "ALTER TABLE IF EXISTS analytics_gold.dim_facturas DROP CONSTRAINT IF EXISTS uq_dim_facturas_codigo_factura",
        "ALTER TABLE IF EXISTS analytics_gold.dim_facturas DROP CONSTRAINT IF EXISTS dim_facturas_pkey"
    ],
    post_hook=[
        "ALTER TABLE analytics_gold.dim_facturas ADD PRIMARY KEY (id_factura)",
        "ALTER TABLE analytics_gold.dim_facturas ADD CONSTRAINT uq_dim_facturas_codigo_factura UNIQUE (codigo_factura)"
    ]
) }}

WITH stg_facturas AS (
    SELECT
        codigo_factura,
        codigo_documento,
        numero_factura,
        comentario_1,
        comentario_2,
        comentario_3,
        id_sucursal,
        codigo_descuento,
        is_nc
    FROM {{ ref('dbt_fenix_facturas')}} ff_0
    WHERE NOT EXISTS (
        SELECT 1
        FROM {{source('features_by_code', 'facturas_excluidas')}} fe_0
        WHERE fe_0.codigo_factura = ff_0.codigo_factura
    )
),

notas_credito AS (
    SELECT distinct  codigo_documento
    FROM {{ ref('dbt_fenix_facturas')}}
    WHERE is_nc
),

-- codigo_descuento de la factura original por codigo_documento, para que las notas de
-- crédito (is_nc) lo hereden en vez de usar el propio (no siempre replica el de la
-- factura que anulan, ver herencia análoga en dbt_fact_facturacion.id_codigo/grupo_vendedor)
codigo_descuento_original AS (
    SELECT
        codigo_documento,
        MAX(codigo_descuento) AS codigo_descuento_original
    FROM stg_facturas
    WHERE NOT is_nc
    GROUP BY codigo_documento
),

camunda_dedup AS (
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

fenix_dedup AS (
    SELECT
        codigo_documento,
        tipo_venta
    FROM (
        SELECT
            t_0.codigo_documento,
            co_0.tipo_venta,
            ROW_NUMBER() OVER (
                PARTITION BY t_0.codigo_documento
                ORDER BY co_0.tipo_venta -- puedes cambiar este criterio
            ) AS rn
        FROM stg_facturas t_0
        LEFT JOIN camunda_dedup co_0
            ON t_0.numero_factura = co_0.numero_factura
        WHERE NOT t_0.is_nc
    ) sub
    WHERE rn = 1
),

enriched_facturas AS (
    SELECT
        t_0.codigo_factura,
        t_0.codigo_documento,
        t_0.numero_factura,
        t_0.comentario_1,
        t_0.comentario_2,
        t_0.comentario_3,
        CASE
            WHEN t_0.is_nc AND cdo_0.codigo_descuento_original IS NOT NULL THEN cdo_0.codigo_descuento_original
            ELSE t_0.codigo_descuento
        END AS codigo_descuento,
        CASE WHEN nc_0.codigo_documento IS NOT NULL THEN 'ANULADO' ELSE 'FACTURADO' END AS estado_factura,
        CASE
            WHEN fo_0.tipo_venta IS NOT NULL THEN fo_0.tipo_venta
            WHEN dc_0.concepto_2 IS NOT NULL THEN dc_0.concepto_2
        ELSE NULL END AS tipo_venta
    FROM stg_facturas t_0
    LEFT JOIN notas_credito nc_0 ON t_0.codigo_documento = nc_0.codigo_documento
    LEFT JOIN fenix_dedup fo_0 ON t_0.codigo_documento = fo_0.codigo_documento
    LEFT JOIN {{ref('dbt_dim_codigos')}} dc_0 ON t_0.comentario_3 = dc_0.codigo
    LEFT JOIN codigo_descuento_original cdo_0 ON t_0.codigo_documento = cdo_0.codigo_documento
)

SELECT
    nextval('analytics_gold.dim_facturas_id_factura_seq') AS id_factura,
    codigo_factura,
    codigo_documento,
    numero_factura,
    comentario_1,
    comentario_2,
    comentario_3,
    codigo_descuento,
    estado_factura,
    tipo_venta
FROM enriched_facturas