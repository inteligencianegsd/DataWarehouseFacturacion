{{ config(
    materialized='table',
    alias='fenix_tranfac'
)}}
SELECT
    creation_date,
    update_date,
    TRIM(unico) AS unico,
    TRIM(numfac) AS codigo_factura,
    TRIM(codart) AS codigo_articulo,
    cantidad_d AS cantidad_articulos,
    precio AS valor_unitario,
    desct AS porcentaje_descuento,
    iva as porcentaje_iva

FROM {{ source("fenix_bronze", "fenix_tranfac") }}