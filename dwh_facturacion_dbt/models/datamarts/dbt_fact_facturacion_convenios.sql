{{ config(
    materialized='view',
    alias='fact_facturacion_convenios'
) }}

with stg_facturas AS (
    SELECT
        f_0.*,
        (f_0.subtotal_articulo + f_0.total_iva) as total_factura

    FROM {{ ref('dbt_fact_facturacion') }}  f_0
    JOIN {{ ref('dbt_dim_codigos') }} dc_0 ON f_0.id_codigo = dc_0.id_codigo
    JOIN {{ref('dbt_dim_facturas')}} df_0 ON df_0.id_factura = f_0.id_factura
    WHERE dc_0.atencion = 'CONVENIOS'
)

SELECT *
FROM stg_facturas