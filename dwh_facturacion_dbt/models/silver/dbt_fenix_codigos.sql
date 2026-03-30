{{config(
    materialized = 'table',
    alias='fenix_codigos'
)}}

WITH cleaned_codigos AS (
    SELECT
        id_codigo,
        UPPER(TRIM(codigo)) AS codigo,
        UPPER(TRIM(codigo_nombre)) AS codigo_nombre,
        UPPER(TRIM(familia_producto)) AS familia_producto,
        UPPER(TRIM(atencion)) AS atencion,
        UPPER(TRIM(venta_dirigida)) AS venta_dirigida,
        UPPER(TRIM(concepto_1)) AS concepto_1,
        UPPER(TRIM(concepto_2)) AS concepto_2,
        UPPER(TRIM(plan)) AS plan,
        UPPER(TRIM(vigencia)) AS vigencia
    FROM {{ source('fenix_bronze', 'fenix_codigos')}}

)

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
    vigencia
FROM cleaned_codigos