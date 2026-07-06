{{ config(
    materialized='view',
    alias='dim_facturas_convenios'
) }}

with stg_facturas AS (
    SELECT DISTINCT df_0.*
    FROM {{ ref('dbt_dim_facturas') }} df_0
    JOIN {{ ref('dbt_fact_facturacion') }} f_0
        ON df_0.id_factura = f_0.id_factura
    WHERE f_0.grupo_vendedor = 'GRUPO CONVENIOS'
)

SELECT *
FROM stg_facturas