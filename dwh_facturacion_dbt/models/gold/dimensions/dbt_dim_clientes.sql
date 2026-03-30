
{{ config(
    materialized='table',
    alias='dim_clientes',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_clientes_id_cliente_seq",
        "ALTER TABLE IF EXISTS analytics_gold.dim_clientes DROP CONSTRAINT IF EXISTS uq_dim_clientes_codigo_cliente",
        "ALTER TABLE IF EXISTS analytics_gold.dim_clientes DROP CONSTRAINT IF EXISTS dim_clientes_pkey"
    ],
    post_hook=[
        "ALTER TABLE analytics_gold.dim_clientes ADD PRIMARY KEY (id_cliente)",
        "ALTER TABLE analytics_gold.dim_clientes ADD CONSTRAINT uq_dim_clientes_codigo_cliente UNIQUE (codigo_cliente)"
    ]
) }}

WITH stg_clientes AS (
    SELECT
        codigo AS codigo_cliente,
        nombre AS nombre_cliente,
        cif,
        is_same_corporate_group
    FROM {{ ref('dbt_fenix_clientes')}}
)

SELECT
    -- Inyectamos el siguiente valor de la secuencia para satisfacer el INSERT de dbt
    nextval('analytics_gold.dim_clientes_id_cliente_seq') AS id_cliente,
    codigo_cliente,
    nombre_cliente,
    cif,
    is_same_corporate_group
FROM stg_clientes