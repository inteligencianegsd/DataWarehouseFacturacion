{{ config(
    materialized='view',
    alias='dim_facturas_convenios'
) }}

with stg_facturas AS (
    SELECT DISTINCT df_0.*
    FROM {{ ref('dbt_dim_facturas') }} df_0
    JOIN {{ ref('dbt_fact_facturacion') }} f_0
        ON df_0.id_factura = f_0.id_factura
    JOIN {{ ref('dbt_dim_codigos') }} dc_0
        ON f_0.id_codigo = dc_0.id_codigo
    WHERE dc_0.atencion = 'CONVENIOS'
)

SELECT *
FROM stg_facturas