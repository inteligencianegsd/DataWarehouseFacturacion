{{ config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='codigo_articulo',
    alias='dim_articulos',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_articulos_id_articulo_seq"
    ],
    post_hook=[
        "DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_dim_articulos_codigo_articulo') THEN
                ALTER TABLE analytics_gold.dim_articulos ADD CONSTRAINT uq_dim_articulos_codigo_articulo UNIQUE (codigo_articulo);
            END IF;
        END $$;",
        "DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'dim_articulos_pkey') THEN
                ALTER TABLE analytics_gold.dim_articulos ADD PRIMARY KEY (id_articulo);
            END IF;
        END $$;"
    ]
) }}

WITH stg_articulos AS (
    SELECT
        dfa_0.codigo AS codigo_articulo,
        dfa_0.nombre AS nombre_articulo,
        dfa_0.vigencia,
        dfa_0.familia,
        dfa_0.tipo_plan,
        ac_0.verificacion_vendedor,
        CASE
            WHEN ac_0.verificacion_vendedor IS NOT NULL THEN TRUE
            ELSE FALSE END
        AS is_codigo_comercial,
        concepto
    FROM {{ ref('dbt_fenix_articulos')}} dfa_0
    LEFT JOIN {{ref('articulos_comercial')}}  ac_0 ON dfa_0.codigo = ac_0.codigo_articulo
)

SELECT
    -- Preserva el id_articulo ya asignado (busca por llave natural en la tabla actual); solo
    -- consume la secuencia para artículos genuinamente nuevos. Ver [[project-secuencias-dimensiones-gold]].
    {% if is_incremental() %}
    COALESCE(existing.id_articulo, nextval('analytics_gold.dim_articulos_id_articulo_seq')) AS id_articulo,
    {% else %}
    nextval('analytics_gold.dim_articulos_id_articulo_seq') AS id_articulo,
    {% endif %}
    sa_0.codigo_articulo,
    sa_0.nombre_articulo,
    sa_0.vigencia,
    sa_0.familia,
    sa_0.tipo_plan,
    sa_0.verificacion_vendedor,
    sa_0.is_codigo_comercial,
    sa_0.concepto
FROM stg_articulos sa_0
{% if is_incremental() %}
LEFT JOIN {{ this }} AS existing ON sa_0.codigo_articulo = existing.codigo_articulo
{% endif %}
WHERE EXISTS (
    SELECT 1
    FROM {{ref('dbt_fenix_tranfac')}} t_0
    WHERE sa_0.codigo_articulo = t_0.codigo_articulo
) OR sa_0.codigo_articulo like 'SF.MAN%'