{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='codigo_vendedor',
    alias='dim_vendedores',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_vendedores_id_vendedor_seq"
    ],
    post_hook=[
        "DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'dim_vendedores_pkey') THEN
                ALTER TABLE analytics_gold.dim_vendedores ADD PRIMARY KEY (id_vendedor);
            END IF;
        END $$;",
        "DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_vendedores_codigo_vendedor') THEN
                ALTER TABLE analytics_gold.dim_vendedores ADD CONSTRAINT uq_dim_vendedores_codigo_vendedor UNIQUE (codigo_vendedor);
            END IF;
        END $$;"
    ]
) }}


WITH stg_vendedores AS (
    SELECT
        codigo AS codigo_vendedor,
        nombre AS nombre_vendedor
    FROM {{ ref('dbt_fenix_vendedores') }}
)


SELECT
    -- Preserva el id_vendedor ya asignado (busca por llave natural en la tabla actual); solo
    -- consume la secuencia para vendedores genuinamente nuevos. Ver [[project-secuencias-dimensiones-gold]].
    {% if is_incremental() %}
    COALESCE(existing.id_vendedor, nextval('analytics_gold.dim_vendedores_id_vendedor_seq')) AS id_vendedor,
    {% else %}
    nextval('analytics_gold.dim_vendedores_id_vendedor_seq') AS id_vendedor,
    {% endif %}
    stg_vendedores.codigo_vendedor,
    stg_vendedores.nombre_vendedor
FROM stg_vendedores
{% if is_incremental() %}
LEFT JOIN {{ this }} AS existing ON stg_vendedores.codigo_vendedor = existing.codigo_vendedor
{% endif %}