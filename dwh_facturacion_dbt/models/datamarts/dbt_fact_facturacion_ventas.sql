{{ config(
    materialized='view',
    alias='fact_facturacion_ventas'
) }}
-- CTE 1: Primer artículo por combinación de vigencia/familia/plan/concepto
WITH articulos_filtrados AS (
    SELECT
        da_0.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                da_0.vigencia,
                da_0.familia,
                da_0.tipo_plan,
                da_0.concepto
            ORDER BY da_0.id_articulo
        ) AS rn
    FROM {{ref('dbt_dim_articulos')}} da_0
    WHERE da_0.codigo_articulo LIKE 'SF.MAN.%'
),

-- CTE 2: Facturas que contienen al menos 1 artículo SF
facturas_sf AS (
    SELECT DISTINCT
        ff_sf.id_factura,
        dc_sf.vigencia,
        dc_sf.familia_producto,
        dc_sf.plan,
        dc_sf.concepto_1
    FROM {{ref('dbt_fact_facturacion')}}  ff_sf
    JOIN {{ref('dbt_dim_codigos')}}       dc_sf ON ff_sf.id_codigo   = dc_sf.id_codigo
    JOIN {{ref('dbt_dim_facturas')}}      df_0  ON ff_sf.id_factura  = df_0.id_factura
    WHERE dc_sf.familia_producto = 'SISTEMA DE FACTURACION'
      --AND df_0.codigo_factura NOT LIKE 'DV%'
),

-- CTE 3: Une facturas SF con el primer artículo que coincida en dimensiones
facturas_sf_con_articulo AS (
    SELECT
        fsf.id_factura,
        af.id_articulo AS id_articulo_sf
    FROM facturas_sf fsf
    -- Busca el primer artículo (rn=1) con la misma vigencia/familia/plan/concepto
    JOIN articulos_filtrados af
        ON  af.vigencia          = fsf.vigencia
        AND af.familia  = fsf.familia_producto
        AND af.tipo_plan              = fsf.plan
        AND af.concepto        = fsf.concepto_1
        AND af.rn                = 1
),

-- CTE 4: Separa registros SF y no-SF antes de agrupar
fact_pre AS (
    SELECT
        ff.id_factura,
        ff.fecha_emision,
        ff.fecha_emision_fenix,
        ff.id_cliente,
        ff.id_sucursal,
        ff.id_codigo,
        ff.grupo_vendedor,
        ff.id_vendedor,

        -- Artículo: SF → id del primer artículo mapeado | no-SF → el propio
        CASE WHEN fsf_a.id_factura IS NOT NULL
                  AND dc.familia_producto = 'SISTEMA DE FACTURACION'
             THEN fsf_a.id_articulo_sf
             ELSE ff.id_articulo
        END                              AS id_articulo,
        ff.cantidad_articulos,
        ff.valor_unitario,
        ff.subtotal_articulo
    FROM {{ref('dbt_fact_facturacion')}}  ff
    JOIN {{ref('dbt_dim_codigos')}}        dc    ON ff.id_codigo  = dc.id_codigo
    LEFT JOIN facturas_sf_con_articulo     fsf_a ON ff.id_factura = fsf_a.id_factura
),

stg_fact_facturacion AS (
    SELECT
        id_factura,
        fecha_emision,
        fecha_emision_fenix,
        id_cliente,
        id_sucursal,
        id_codigo,
        id_vendedor,
        grupo_vendedor,
        id_articulo,
        cantidad_articulos,
        SUM(valor_unitario)    AS valor_unitario,
        SUM(subtotal_articulo) AS subtotal_articulo
    FROM fact_pre
    GROUP BY
        id_factura,
        fecha_emision,
        fecha_emision_fenix,
        id_cliente,
        id_vendedor,
        id_sucursal,
        id_codigo,
        grupo_vendedor,
        id_articulo,
        cantidad_articulos
)


SELECT * FROM stg_fact_facturacion