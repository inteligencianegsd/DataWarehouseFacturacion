SELECT DISTINCT TRIM(f.numfac) AS codigo_factura, 'TOTAL IVA CERO' AS motivo
FROM security_data.facturas f
WHERE f.total_iva = 0 and f.numfac!= ''