{{ config(
    materialized='view',
    alias='fact_facturacion_ventas'
) }}

-- CTE 1: Identifica qué facturas contienen al menos 1 artículo de SF
WITH facturas_sf AS (
    SELECT DISTINCT ff_sf.id_factura, df_0.comentario_3
    FROM {{ref('dbt_fact_facturacion')}} ff_sf
    JOIN {{ref('dbt_dim_codigos')}} dc_sf ON ff_sf.id_codigo = dc_sf.id_codigo
    JOIN {{ref('dbt_dim_facturas')}} df_0 ON ff_sf.id_factura = df_0.id_factura
    WHERE dc_sf.familia_producto = 'SISTEMA DE FACTURACION'
),

stg_fact_facturacion AS (
    SELECT
        ff.id_factura,
        ff.fecha_emision,
        ff.id_cliente,
        ff.id_sucursal,

        CASE
            WHEN fsf.id_factura IS NOT NULL THEN da_0.id_articulo
            ELSE ff.id_articulo
        END                               AS id_articulo,

        ff.cantidad_articulos             AS cantidad_articulos,
        SUM(ff.valor_unitario)            AS valor_unitario,
        SUM(ff.subtotal_articulo)         AS subtotal_articulo,
        grupo_vendedor

    FROM {{ref('dbt_fact_facturacion')}} ff
    LEFT JOIN facturas_sf fsf ON ff.id_factura = fsf.id_factura
    LEFT JOIN {{ref('dbt_dim_articulos')}} da_0 ON fsf.comentario_3 = da_0.codigo_articulo

    GROUP BY
        ff.id_factura,
        ff.fecha_emision,
        ff.id_cliente,
        ff.id_sucursal,
        grupo_vendedor,
        ff.cantidad_articulos,
        CASE
            WHEN fsf.id_factura IS NOT NULL THEN da_0.id_articulo
            ELSE ff.id_articulo
        END
)
SELECT *

FROM stg_fact_facturacion