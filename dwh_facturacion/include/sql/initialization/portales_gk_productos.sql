SELECT
   id_cli AS id_tramite,
   CASE 
	    WHEN cedula IS NULL THEN LEFT(ruc, 10)
	    ELSE cedula
	END AS cedula, 
	case when fecha_aprob IS NULL then fecha_registro ELSE fecha_aprob END AS fecha_aprobacion,
	case when fecha_aprob IS NULL then fecha_registro ELSE fecha_aprob END AS fecha_factura,
	facturaEmitida AS factura, 
	ruc AS ruc,
	tipoPersona AS tipo_firma,
	serial AS serial_firma,
	fecha_creacion AS "fecha_inicio_tramite", 
	ruc AS ruc_aux,
	CASE 
	    WHEN tipo_servicio = 'SIN_FIRMA' THEN 'SF Sin Firma'
	    ELSE 'SF Con FIRMA' 
	END AS producto,
	1   AS sf_control,
	'APROBADO' as estado
	 
FROM 
    SistemaFacturacion.tb_registro_cli_gt 
WHERE 
    estado IN (1, 5, 4, 3) 
    AND tipo_servicio <> "ADICIONAL"
    AND ap1 NOT LIKE "%prueb%"
    AND ap2 NOT LIKE "%prueb%"
    AND nombre NOT LIKE "%prueb%"
    
    AND anos != '2M'
    ORDER BY  cedula