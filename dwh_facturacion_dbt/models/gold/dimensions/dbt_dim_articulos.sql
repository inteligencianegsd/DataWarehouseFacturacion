{{ config(
    materialized='table',
    alias='dim_articulos',
    pre_hook=[
        "CREATE SEQUENCE IF NOT EXISTS analytics_gold.dim_articulos_id_articulo_seq",
        "ALTER TABLE IF EXISTS analytics_gold.dim_articulos DROP CONSTRAINT IF EXISTS uq_dim_articulos_codigo_articulo",
        "ALTER TABLE IF EXISTS analytics_gold.dim_articulos DROP CONSTRAINT IF EXISTS dim_articulos_pkey"
    ],
    post_hook=[
        "ALTER TABLE analytics_gold.dim_articulos ADD CONSTRAINT uq_dim_articulos_codigo_articulo UNIQUE (codigo_articulo)",
        "ALTER TABLE analytics_gold.dim_articulos ADD PRIMARY KEY (id_articulo)"
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
    -- Reemplazamos nextval por la generación del Hash MD5 convertido a UUID
    nextval('analytics_gold.dim_articulos_id_articulo_seq') AS id_articulo,
    codigo_articulo,
    nombre_articulo,
    vigencia,
    familia,
    tipo_plan,
    verificacion_vendedor,
    is_codigo_comercial,
    concepto
FROM stg_articulos sa_0
WHERE EXISTS (
    SELECT 1
    FROM {{ref('dbt_fenix_tranfac')}} t_0
    WHERE sa_0.codigo_articulo = t_0.codigo_articulo
) OR codigo_articulo like 'SF.MAN%'