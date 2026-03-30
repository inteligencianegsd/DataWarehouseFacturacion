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
        codigo_descuento
    FROM {{ ref('dbt_fenix_facturas')}} ff_0
    WHERE NOT EXISTS (
        SELECT 1
        FROM {{ref('facturas_excluidas')}} fe_0
        WHERE fe_0.codigo_documento = ff_0.codigo_documento
    )
),

notas_credito AS (
    SELECT distinct  codigo_documento
    FROM {{ ref('dbt_fenix_facturas')}}
    WHERE codigo_factura LIKE 'DV%'
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

enriched_facturas AS (
    SELECT
        t_0.codigo_factura,
        t_0.codigo_documento,
        t_0.numero_factura,
        t_0.comentario_1,
        t_0.comentario_2,
        t_0.comentario_3,
        t_0.codigo_descuento,
        CASE WHEN nc_0.codigo_documento IS NOT NULL THEN 'ANULADO' ELSE 'FACTURADO' END AS estado_factura,
        co_0.tipo_emision as tipo_venta
    FROM stg_facturas t_0
    LEFT JOIN notas_credito nc_0 ON t_0.codigo_documento = nc_0.codigo_documento
    LEFT JOIN camunda_dedup co_0 ON t_0.numero_factura = co_0.numero_factura
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