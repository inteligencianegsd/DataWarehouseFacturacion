{{ config(
    materialized='table',
    alias='dim_codigos',
    pre_hook=[
        "ALTER TABLE IF EXISTS analytics_gold.dim_codigos DROP CONSTRAINT IF EXISTS uq_dim_codigos_codigo",
        "ALTER TABLE IF EXISTS analytics_gold.dim_codigos DROP CONSTRAINT IF EXISTS dim_codigos_pkey"
    ],
    post_hook=[
        "ALTER TABLE analytics_gold.dim_codigos ADD PRIMARY KEY (id_codigo)",
        "ALTER TABLE analytics_gold.dim_codigos ADD CONSTRAINT uq_dim_codigos_codigo UNIQUE (codigo)"
    ]
) }}

WITH stg_codigos AS (
    SELECT
        id_codigo,
        codigo,
        codigo_nombre,
        familia_producto,
        atencion,
        venta_dirigida,
        concepto_1,
        concepto_2,
        plan,
        REPLACE(vigencia, 'VIGENCIA ', '') AS vigencia
    FROM {{ref('dbt_fenix_codigos')}} dco_0
--    WHERE EXISTS (
--        SELECT 1
--        FROM {{ref('dbt_fenix_facturas')}} f_0
--        WHERE f_0.comentario_3 = dco_0.codigo
--    )

)

SELECT
    DISTINCT
    id_codigo,
    codigo,
    codigo_nombre,
    familia_producto,
    atencion,
    venta_dirigida,
    concepto_1,
    concepto_2,
    plan,
    vigencia
FROM stg_codigos
