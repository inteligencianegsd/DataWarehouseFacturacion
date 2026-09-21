{{config(
    materialized='table',
    alias='fact_estado_resultados',
)}}

-- Traduccion 1:1 de la logica de Estado de Resultados que antes vivia en Power Query
-- (ODBC directo a Fenix64). Los codasi/exclusiones especiales por cierre de ano fiscal
-- ya no estan hardcodeados aqui: viven en los seeds contable_cuentas_especiales y
-- contable_exclusiones_codasi, editables sin tocar este modelo cada cierre de ano.

WITH rencon_enccon AS (
    SELECT
        r.codigo_cuenta,
        r.importe,
        r.codigo_asiento,
        e.fecha_asiento AS fecha
    FROM {{ref('dbt_fenix_rencon')}} r
    JOIN {{ref('dbt_fenix_enccon')}} e ON r.codigo_asiento = e.codigo_asiento
    WHERE e.fecha_asiento >= '2024-01-01'
),

cuentas_especiales AS (
    SELECT anio, seccion, codasi
    FROM {{ref('contable_cuentas_especiales')}}
),

exclusiones_codasi AS (
    SELECT anio, seccion, codasi_patron, tipo_match
    FROM {{ref('contable_exclusiones_codasi')}}
),

-- 1. PROVISIONES: asiento de cierre del ano, se invierte el signo
provisiones AS (
    SELECT
        r.fecha,
        -SUM(r.importe) AS valor,
        'PROVISIONES' AS cuenta
    FROM rencon_enccon r
    WHERE LEFT(r.codigo_cuenta, 1) = '4'
      AND EXISTS (
          SELECT 1 FROM cuentas_especiales ce
          WHERE ce.seccion = 'PROVISIONES'
            AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
            AND ce.codasi = r.codigo_asiento
      )
    GROUP BY r.fecha
),

-- Reversion de la provision del mes anterior: signo invertido y fecha -1 mes
provisiones_reversion AS (
    SELECT
        (fecha - INTERVAL '1 month')::date AS fecha,
        -valor AS valor,
        'PROVISIONES' AS cuenta
    FROM provisiones
),

-- 2. REGULACIONES: asiento(s) de regulacion del ano, se invierte el signo
regulaciones AS (
    SELECT
        r.fecha,
        -SUM(r.importe) AS valor,
        'REGULACIONES' AS cuenta
    FROM rencon_enccon r
    WHERE LEFT(r.codigo_cuenta, 1) = '4'
      AND EXISTS (
          SELECT 1 FROM cuentas_especiales ce
          WHERE ce.seccion = 'REGULACIONES'
            AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
            AND ce.codasi = r.codigo_asiento
      )
    GROUP BY r.fecha
),

-- 3. VENTA ACTIVOS: cuentas fijas del plan de cuentas (no varian por ano)
venta_activos AS (
    SELECT
        r.fecha,
        CASE
            WHEN EXTRACT(MONTH FROM r.fecha) = 12 AND ce.codasi IS NOT NULL
                THEN SUM(CASE WHEN r.codigo_asiento = ce.codasi THEN r.importe ELSE 0 END) - SUM(r.importe)
            ELSE SUM(r.importe)
        END AS valor,
        'VENTA ACTIVOS' AS cuenta
    FROM rencon_enccon r
    LEFT JOIN cuentas_especiales ce
        ON ce.seccion = 'CIERRE_DICIEMBRE' AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
    WHERE r.codigo_cuenta IN ('7.1.1.01.02.002', '7.1.1.01.02.006')
    GROUP BY r.fecha, ce.codasi
),

-- 4. COSTOS: cuentas clase 5
costos AS (
    SELECT
        r.fecha,
        CASE
            WHEN EXTRACT(MONTH FROM r.fecha) = 12 AND ce.codasi IS NOT NULL
                THEN SUM(CASE WHEN r.codigo_asiento = ce.codasi THEN r.importe ELSE 0 END) - SUM(r.importe)
            ELSE -SUM(r.importe)
        END AS valor,
        'COSTOS' AS cuenta
    FROM rencon_enccon r
    LEFT JOIN cuentas_especiales ce
        ON ce.seccion = 'CIERRE_DICIEMBRE' AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
    WHERE LEFT(r.codigo_cuenta, 1) = '5'
    GROUP BY r.fecha, ce.codasi
),

-- 5. GASTOS: cuentas clase 6, excluyendo 2 cuentas fijas y los codasi puntuales del seed
gastos AS (
    SELECT
        r.fecha,
        CASE
            WHEN EXTRACT(MONTH FROM r.fecha) = 12 AND ce.codasi IS NOT NULL
                THEN SUM(CASE WHEN r.codigo_asiento = ce.codasi THEN r.importe ELSE 0 END) - SUM(r.importe)
            ELSE -SUM(r.importe)
        END AS valor,
        'GASTOS' AS cuenta
    FROM rencon_enccon r
    LEFT JOIN cuentas_especiales ce
        ON ce.seccion = 'CIERRE_DICIEMBRE' AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
    WHERE LEFT(r.codigo_cuenta, 1) = '6'
      AND r.codigo_cuenta NOT IN ('6.1.2.02.01.006', '6.1.2.02.01.007')
      AND NOT EXISTS (
          SELECT 1 FROM exclusiones_codasi ex
          WHERE ex.seccion = 'GASTOS'
            AND ex.anio = EXTRACT(YEAR FROM r.fecha)::integer
            AND (
                (ex.tipo_match = 'EXACTO' AND r.codigo_asiento = ex.codasi_patron)
                OR (ex.tipo_match = 'PREFIJO' AND r.codigo_asiento LIKE ex.codasi_patron || '%')
            )
      )
    GROUP BY r.fecha, ce.codasi
),

-- 6. OTROS INGRESOS Y GASTOS: cuentas clase 7
otros_ingresos_gastos AS (
    SELECT
        r.fecha,
        CASE
            WHEN EXTRACT(MONTH FROM r.fecha) = 12 AND ce.codasi IS NOT NULL
                THEN SUM(CASE WHEN r.codigo_asiento = ce.codasi THEN r.importe ELSE 0 END) - SUM(r.importe)
            ELSE -SUM(r.importe)
        END AS valor,
        'OTROS INGRESOS Y GASTOS' AS cuenta
    FROM rencon_enccon r
    LEFT JOIN cuentas_especiales ce
        ON ce.seccion = 'CIERRE_DICIEMBRE' AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
    WHERE LEFT(r.codigo_cuenta, 1) = '7'
    GROUP BY r.fecha, ce.codasi
),

-- 7. DEPRECIACIONES / AMORTIZACIONES: cuentas fijas del plan de cuentas
depre_amor AS (
    SELECT
        r.fecha,
        CASE
            WHEN EXTRACT(MONTH FROM r.fecha) = 12 AND ce.codasi IS NOT NULL
                THEN SUM(CASE WHEN r.codigo_asiento = ce.codasi THEN r.importe ELSE 0 END) - SUM(r.importe)
            ELSE -SUM(r.importe)
        END AS valor,
        'DEPRE/AMOR' AS cuenta
    FROM rencon_enccon r
    LEFT JOIN cuentas_especiales ce
        ON ce.seccion = 'CIERRE_DICIEMBRE' AND ce.anio = EXTRACT(YEAR FROM r.fecha)::integer
    WHERE r.codigo_cuenta IN ('6.1.2.02.01.020', '6.1.2.02.01.021', '5.8.1.03.02.007', '5.8.1.03.03.021')
      AND NOT EXISTS (
          SELECT 1 FROM exclusiones_codasi ex
          WHERE ex.seccion = 'DEPRE_AMOR'
            AND ex.anio = EXTRACT(YEAR FROM r.fecha)::integer
            AND (
                (ex.tipo_match = 'EXACTO' AND r.codigo_asiento = ex.codasi_patron)
                OR (ex.tipo_match = 'PREFIJO' AND r.codigo_asiento LIKE ex.codasi_patron || '%')
            )
      )
    GROUP BY r.fecha, ce.codasi
),

-- 8. INGRESOS: no viene de contabilidad, viene del datawarehouse de facturacion
ingresos AS (
    SELECT
        fecha_emision AS fecha,
        SUM(subtotal_articulo) AS valor,
        'INGRESOS' AS cuenta
    FROM {{ref('dbt_fact_facturacion')}}
    GROUP BY fecha_emision
)

SELECT fecha, valor, cuenta FROM provisiones
UNION ALL
SELECT fecha, valor, cuenta FROM provisiones_reversion
UNION ALL
SELECT fecha, valor, cuenta FROM regulaciones
UNION ALL
SELECT fecha, valor, cuenta FROM venta_activos
UNION ALL
SELECT fecha, valor, cuenta FROM costos
UNION ALL
SELECT fecha, valor, cuenta FROM gastos
UNION ALL
SELECT fecha, valor, cuenta FROM otros_ingresos_gastos
UNION ALL
SELECT fecha, valor, cuenta FROM depre_amor
UNION ALL
SELECT fecha, valor, cuenta FROM ingresos
