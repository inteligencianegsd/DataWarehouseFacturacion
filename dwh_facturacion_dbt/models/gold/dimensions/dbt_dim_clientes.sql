
{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='codigo_cliente',
    alias='dim_clientes',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_clientes_id_cliente_seq"
    ],
    post_hook=[
        "DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'dim_clientes_pkey') THEN
                ALTER TABLE analytics_gold.dim_clientes ADD PRIMARY KEY (id_cliente);
            END IF;
        END $$;",
        "DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_clientes_codigo_cliente') THEN
                ALTER TABLE analytics_gold.dim_clientes ADD CONSTRAINT uq_dim_clientes_codigo_cliente UNIQUE (codigo_cliente);
            END IF;
        END $$;"
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
    -- Preserva el id_cliente ya asignado (busca por llave natural en la tabla actual); solo
    -- consume la secuencia para clientes genuinamente nuevos. Ver [[project-secuencias-dimensiones-gold]].
    {% if is_incremental() %}
    COALESCE(existing.id_cliente, nextval('analytics_gold.dim_clientes_id_cliente_seq')) AS id_cliente,
    {% else %}
    nextval('analytics_gold.dim_clientes_id_cliente_seq') AS id_cliente,
    {% endif %}
    stg_clientes.codigo_cliente,
    stg_clientes.nombre_cliente,
    stg_clientes.cif,
    stg_clientes.is_same_corporate_group
FROM stg_clientes
{% if is_incremental() %}
LEFT JOIN {{ this }} AS existing ON stg_clientes.codigo_cliente = existing.codigo_cliente
{% endif %}