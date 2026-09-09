{{ config(
    materialized='table',
    alias='dim_vendedores',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_vendedores_id_vendedor_seq",
        "ALTER TABLE IF EXISTS analytics_gold.dim_vendedores DROP CONSTRAINT IF EXISTS uq_dim_vendedores_codigo_vendedor",
        "ALTER TABLE IF EXISTS analytics_gold.dim_vendedores DROP CONSTRAINT IF EXISTS dim_vendedores_pkey"
    ],
    post_hook=[
        "ALTER TABLE analytics_gold.dim_vendedores ADD PRIMARY KEY (id_vendedor)",
        "ALTER TABLE analytics_gold.dim_vendedores ADD CONSTRAINT uq_dim_vendedores_codigo_vendedor UNIQUE (codigo_vendedor)"
    ]
) }}


WITH stg_vendedores AS (
    SELECT
        codigo AS codigo_vendedor,
        nombre AS nombre_vendedor
    FROM {{ ref('dbt_fenix_vendedores') }}
)


SELECT
    -- Inyectamos el siguiente valor de la secuencia para satisfacer el INSERT de dbt
    nextval('analytics_gold.dim_vendedores_id_vendedor_seq') AS id_vendedor,
    codigo_vendedor,
    nombre_vendedor
FROM stg_vendedores