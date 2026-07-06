{{ config(
    materialized='view',
    alias='fact_facturacion_convenios'
) }}

with stg_facturas AS (
    SELECT
        f_0.*,
        (f_0.subtotal_articulo + f_0.total_iva) as total_factura

    FROM {{ ref('dbt_fact_facturacion') }}  f_0
    JOIN {{ref('dbt_dim_facturas')}} df_0 ON df_0.id_factura = f_0.id_factura
    WHERE f_0.grupo_vendedor = 'GRUPO CONVENIOS'
)

SELECT *
FROM stg_facturas