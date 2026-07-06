{{ config(
    materialized='view',
    alias='dim_clientes_convenios'
) }}

with stg_clientes AS (
    SELECT DISTINCT dcl_0.*
    FROM {{ ref('dbt_dim_facturas') }} df_0
    JOIN {{ ref('dbt_fact_facturacion') }} f_0
        ON df_0.id_factura = f_0.id_factura
    JOIN {{ref('dbt_dim_clientes')}} dcl_0
        ON f_0.id_cliente = dcl_0.id_cliente
    WHERE f_0.grupo_vendedor = 'GRUPO CONVENIOS' AND df_0.estado_factura = 'FACTURADO'
)

SELECT *
FROM stg_clientes