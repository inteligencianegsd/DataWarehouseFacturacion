{{config(
    materialized='table',
    alias='fact_facturacion',
)}}

WITH facturas_comercial AS (
    SELECT
       DISTINCT codigo_documento
    FROM {{ref('dbt_fenix_facturas')}} f_0
    JOIN {{ref('dbt_fenix_tranfac')}} t_0 ON f_0.codigo_factura = t_0.codigo_factura
    JOIN {{ref('dbt_dim_articulos')}} da_0 ON t_0.codigo_articulo = da_0.codigo_articulo
    JOIN {{ref('dbt_dim_clientes')}} dc_0 ON f_0.codigo_cliente = dc_0.codigo_cliente
    JOIN {{ref('dbt_dim_vendedores')}} dv_0 ON f_0.codigo_vendedor = dv_0.codigo_vendedor
    LEFT JOIN {{ref('vendedores_comercial')}} vc_0 ON dv_0.codigo_vendedor = vc_0.codigo_vendedor
    WHERE
    f_0.codigo_factura NOT LIKE 'DV%' AND (
        (da_0.is_codigo_comercial AND NOT da_0.verificacion_vendedor)
        OR (da_0.is_codigo_comercial AND da_0.verificacion_vendedor AND f_0.fecha_emision BETWEEN vc_0.fecha_inicio and  vc_0.fecha_fin AND f_0.comentario_2 NOT LIKE '%RENOVACION%')
        OR (dc_0.codigo_cliente = '1291790310' AND f_0.fecha_emision >= '2025-09-01')
        OR f_0.comentario_3 = 'F.E.F.A.V.'
        OR (f_0.comentario_3 = 'COMERCIAL' AND NOT da_0.verificacion_vendedor)
        OR (f_0.comentario_3 = 'COMERCIAL' AND da_0.verificacion_vendedor AND f_0.comentario_2 NOT LIKE '%RENOVACION%')
        OR EXISTS (
            SELECT 1
            FROM {{ref('reasignacion_comercial')}} rc_0
            WHERE rc_0.codigo_documento = f_0.codigo_documento
        )
    )
),

facturas_convenios AS (
    SELECT DISTINCT id_factura, dco_default_convenios.id_codigo, codigo_documento
    FROM {{ref('dbt_dim_facturas')}} f_0
    JOIN {{ref('dbt_dim_codigos')}} dco_default_convenios ON dco_default_convenios.codigo = 'CONVE.FACT.MANUAL'
    WHERE f_0.codigo_descuento LIKE '%ALIANZA%'
),

facturas_agentes AS (
    SELECT DISTINCT codigo_documento
    FROM {{ref('dbt_fenix_facturas')}} f_0
    JOIN {{ref('dbt_dim_vendedores')}} dv_0 ON f_0.codigo_vendedor = dv_0.codigo_vendedor
    LEFT JOIN {{ref('vendedores_agentes')}} va_0 ON dv_0.codigo_vendedor = va_0.codigo_vendedor
    WHERE f_0.comentario_3 LIKE '%AGENT%'
    OR f_0.comentario_2 LIKE '%AGENT%'
    OR va_0.codigo_vendedor IS NOT NULL
),

stg_fact_facturacion AS (
    SELECT
        df_0.id_factura,
        f_0.fecha_emision as fecha_emision_fenix,
        -- Desplaza un mes atrás si la factura está en el seed
        CASE
            WHEN rpf_0.numero_factura IS NOT NULL
            THEN (f_0.fecha_emision - INTERVAL '1 month')::date
            ELSE f_0.fecha_emision
        END AS fecha_emision,
        dc_0.id_cliente,
        dv_0.id_vendedor,
        da_0.id_articulo,
        f_0.id_sucursal,
        CASE
            WHEN dco_0.id_codigo IS NOT NULL THEN dco_0.id_codigo
            WHEN fcon_0.id_factura IS NOT NULL THEN fcon_0.id_codigo
            -- WHEN f_0.codigo_descuento LIKE '%ALIANZA%' THEN dco_default_convenios.id_codigo
            ELSE dco_default.id_codigo
        END AS id_codigo,

        t_0.cantidad_articulos,
        t_0.valor_unitario,
        t_0.porcentaje_descuento,
        t_0.cantidad_articulos * t_0.valor_unitario * (100 - t_0.porcentaje_descuento) / 100 AS subtotal_articulo,
        t_0.cantidad_articulos * t_0.valor_unitario * (t_0.porcentaje_descuento) / 100 AS descuento_articulo,
        f_0.total - f_0.total_iva AS total_sin_iva,
        t_0.porcentaje_iva,


        CASE
            WHEN rgv_0.codigo_documento IS NOT NULL THEN rgv_0.grupo_asignado
            WHEN rd_0.grupo_vendedor_reasignado IS NOT NULL AND f_0.comentario_3 LIKE '%TERCER%' AND da_0.familia IN ('FIRMAS ELECTRONICAS', 'SISTEMA DE FACTURACION') THEN grupo_vendedor_reasignado
--            WHEN f_0.comentario_3 like '%COMERCIAL%' THEN 'COMERCIAL'
            WHEN (da_0.familia = 'LICENCIAS' AND dc_0.is_same_corporate_group) THEN 'LICENCIAS TELCONET'
            WHEN (f_0.comentario_3 like '%TERCER%' AND da_0.familia IN ('FIRMAS ELECTRONICAS', 'SISTEMA DE FACTURACION')) THEN 'GRUPO TERCEROS'
            WHEN f_0.comentario_3 like '%DISTRIBUI%' THEN 'GRUPO DISTRIBUIDORES'
            WHEN fa_0.codigo_documento IS NOT NULL THEN 'GRUPO AGENTES'
            WHEN dc_0.codigo_cliente = '1792496136' THEN 'GRUPO GEEKTECH'
            WHEN fc_0.codigo_documento IS NOT NULL THEN 'COMERCIAL'
--            WHEN da_0.codigo_articulo = 'F.E.F.A.V.' THEN 'COMERCIAL'
--            WHEN da_0.is_codigo_comercial AND NOT da_0.verificacion_vendedor  THEN 'COMERCIAL'
--            WHEN da_0.is_codigo_comercial AND da_0.verificacion_vendedor
--                AND f_0.fecha_emision BETWEEN vc_0.fecha_inicio and  vc_0.fecha_fin AND f_0.comentario_2 NOT LIKE '%RENOVACION%' THEN 'COMERCIAL'
            WHEN f_0.grupo_vendedor_temp IS NOT NULL then grupo_vendedor_temp
            ELSE 'GRUPO SECURITY DATA'
        END AS grupo_vendedor


    FROM {{ref('dbt_fenix_facturas')}} f_0
    JOIN {{ref('dbt_fenix_tranfac')}} t_0 ON f_0.codigo_factura = t_0.codigo_factura
    JOIN {{ref('dbt_dim_facturas')}} df_0 ON f_0.codigo_factura = df_0.codigo_factura
    JOIN {{ref('dbt_dim_clientes')}} dc_0 ON f_0.codigo_cliente = dc_0.codigo_cliente
    JOIN {{ref('dbt_dim_vendedores')}} dv_0 ON f_0.codigo_vendedor = dv_0.codigo_vendedor
    JOIN {{ref('dbt_dim_articulos')}} da_0 ON t_0.codigo_articulo = da_0.codigo_articulo
    LEFT JOIN {{ref('dbt_dim_codigos')}} dco_0 ON f_0.comentario_3 = dco_0.codigo
    --LEFT JOIN {{ref('dbt_dim_codigos')}} dco_default_convenios ON dco_default_convenios.codigo = 'CONVE.FACT.MANUAL'
    LEFT JOIN facturas_convenios fcon_0 ON df_0.codigo_documento = fcon_0.codigo_documento
    LEFT JOIN {{ref('dbt_dim_codigos')}} dco_default ON dco_default.codigo = 'MANUAL.FACT.MANUAL'
    LEFT JOIN {{(ref('reasignacion_periodo_fiscal'))}} rpf_0 ON f_0.numero_factura = rpf_0.numero_factura
    --LEFT JOIN {{ref('vendedores_comercial')}} vc_0 ON dv_0.codigo_vendedor = vc_0.codigo_vendedor
    LEFT JOIN facturas_comercial fc_0 on f_0.codigo_documento = fc_0.codigo_documento
    LEFT JOIN facturas_agentes fa_0 on f_0.codigo_documento = fa_0.codigo_documento
    LEFT JOIN {{ref('reasignacion_grupo_vendedor')}} rgv_0 ON f_0.codigo_documento = rgv_0.codigo_documento
    LEFT JOIN {{ref('reasignacion_distribuidores')}} rd_0 ON dc_0.codigo_cliente = rd_0.codigo_cliente AND f_0.fecha_emision >= rd_0.fecha_cambio
    WHERE NOT EXISTS (
        SELECT 1
        FROM {{source('features_by_code', 'facturas_excluidas')}} fe_0
        WHERE fe_0.codigo_factura = f_0.codigo_factura
    )

),

stg_fact_facturacion_diferencia AS (
    SELECT
        *,
        SUM(subtotal_articulo) OVER (PARTITION BY id_factura) AS suma_subtotales,
        -- Diferencia a distribuir por factura
        total_sin_iva - SUM(subtotal_articulo) OVER (PARTITION BY id_factura) AS diferencia
    FROM stg_fact_facturacion
),

stg_fact_facturacion_correccion AS (
    SELECT
        *,
        -- Peso proporcional de cada línea dentro de la factura
        CASE
            WHEN suma_subtotales = 0 THEN 0
            ELSE subtotal_articulo / suma_subtotales
        END AS peso_proporcional,

        -- Ajuste proporcional redondeado a 2 decimales


         (subtotal_articulo / NULLIF(suma_subtotales, 0)) * diferencia AS ajuste_centavos
    FROM stg_fact_facturacion_diferencia
),

stg_fact_subtotal AS (
    SELECT
        id_factura,
        fecha_emision,
        id_cliente,
        id_vendedor,
        id_articulo,
        id_sucursal,
        id_codigo,
        cantidad_articulos,
        valor_unitario,
        porcentaje_descuento,
        fecha_emision_fenix,
        case
            when  diferencia <> 0 then ROUND(subtotal_articulo + ajuste_centavos, 2)
            else subtotal_articulo
        END AS subtotal_articulo,
        porcentaje_iva,

    --  Validación (debería dar 0 o muy cercano)
    --  SUM(subtotal_articulo + ajuste_centavos) OVER (PARTITION BY id_factura) - total_sin_iva AS residuo_control,
        grupo_vendedor,
        descuento_articulo
    FROM stg_fact_facturacion_correccion
),
stg_fact_iva_articulo AS (
    SELECT
        *,
        ROUND(sfs_0.subtotal_articulo * sfs_0.porcentaje_iva / 100, 2) AS total_iva
    FROM stg_fact_subtotal sfs_0

)

SELECT
    id_factura,
    fecha_emision,
    id_cliente,
    id_vendedor,
    id_articulo,
    id_sucursal,
    id_codigo,
    cantidad_articulos,
    valor_unitario,
    porcentaje_descuento,
    porcentaje_iva,
    grupo_vendedor,
    descuento_articulo,
    subtotal_articulo,
    total_iva,
    fecha_emision_fenix

FROM stg_fact_iva_articulo