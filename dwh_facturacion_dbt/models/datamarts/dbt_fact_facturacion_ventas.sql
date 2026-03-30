{{ config(
    materialized='view',
    alias='fact_facturacion_ventas'
) }}

with stg_facturas AS (
    SELECT f_0.*
    FROM {{ ref('dbt_fact_facturacion') }}  f_0
    JOIN {{ ref('dbt_dim_codigos') }} dc_0 ON f_0.id_codigo = dc_0.id_codigo
    WHERE dc_0.atencion = 'CONVENIOS' AND df_0.estado_factura = 'FACTURADO'
)

SELECT *
FROM stg_facturas