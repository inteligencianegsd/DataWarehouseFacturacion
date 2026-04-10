SELECT 
	id_pn AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_pn AS ruc,
	'PN'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	CONCAT(cedula, '001') AS ruc_aux,
	medio,
	0   AS sf_control,
	'FIRMA' AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Subca1.persona_natural
WHERE
	estado_pn IN (1, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_me AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_empresa AS ruc,
	'ME'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	ruc_empresa AS ruc_aux,
	medio,
	0   AS sf_control,
	'FIRMA' AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Subca1.miembro_empresa
WHERE
	estado_me IN (1, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_rl AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_empresa AS ruc,
	'RL'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	ruc_empresa AS ruc_aux,
	medio,
	0   AS sf_control,
	'FIRMA' AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Subca1.representante_legal
WHERE
	estado_rl IN (1, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_me AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_empresa AS ruc,
	'ME'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	ruc_empresa AS ruc_aux,
	medio,
	sf_control,
	CASE
	WHEN sf_control = 1 THEN 'SF Con FIRMA'
	ELSE 'FIRMA'
	END AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Subca2.miembro_empresa
WHERE
	estado_me IN (1, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_rl AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_empresa AS ruc,
	'RL'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	ruc_empresa AS ruc_aux,
	medio,
	sf_control,
	CASE
	WHEN sf_control = 1 THEN 'SF Con FIRMA'
	ELSE 'FIRMA'
	END AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Subca2.representante_legal
WHERE
	estado_rl IN (1, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_pn AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_pn AS ruc,
	'PN'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	CONCAT(cedula, '001') AS ruc_aux,
	medio,
	0   AS sf_control,
	'FIRMA' AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Token.persona_natural
WHERE
	estado_pn IN (1, 4, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_me AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_empresa AS ruc,
	'ME'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	ruc_empresa AS ruc_aux,
	medio,
	0   AS sf_control,
	'FIRMA' AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Token.miembro_empresa
WHERE
	estado_me IN (1, 4, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_rl AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_empresa AS ruc,
	'RL'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	ruc_empresa AS ruc_aux,
	medio,
	0   AS sf_control,
	'FIRMA' AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Token.representante_legal
WHERE
	estado_rl IN (1, 4, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_pn AS id_tramite,
	cedula,
	fecha_aprob AS fecha_aprobacion,
	fecha_aprob AS fecha_factura,
	factura,
	ruc_pn AS ruc,
	'PN'   AS tipo_firma,
	SERIAL AS serial_firma,
	fecha_creacion AS fecha_inicio_tramite,
	CONCAT(cedula, '001') AS ruc_aux,
	medio,
	sf_control,
	CASE
	WHEN sf_control = 1 THEN 'SF Con FIRMA'
	ELSE 'FIRMA'
	END AS producto,
	'APROBADO' as estado
FROM
	Certificados_Electronicos_Subca2.persona_natural
WHERE
	estado_pn IN (1, 5)
	AND nombre NOT LIKE '%prueb%'
	AND ap1 NOT LIKE '%prueb%'
	AND ap2 NOT LIKE '%prueb%'
	AND nombre NOT LIKE '%test%'
	AND ap1 NOT LIKE '%test%'
	AND ap2 NOT LIKE '%test%'
	AND fecha_creacion > '0000-00-00 00:00:00'

UNION

SELECT
	id_sfsf AS id_tramite,
	cedula, 
	fechaAprob AS fecha_aprobacion,
	fechaAprob AS fecha_factura,
	facturaEmitida AS factura, 
	'SF Sin Firma' AS producto,
	fecha_creacion AS fecha_inicio_tramite, 
	'SF Sin Firma' AS mediocam,
	ruc, 
	tipoPersona AS tipo_firma,
	numserie   AS serial_firma, 
	1   AS sf_control, 
	ruc AS ruc_aux,
	'APROBADO' as estado
FROM 
	Certificados_Electronicos_Subca2.tb_securityFSinFirma
WHERE 
	estado IN (1, 5)
	AND nombres NOT LIKE '%prueb%'
	AND nombres NOT LIKE '%test%'
	AND fechaAprob IS NOT NULL 
	AND fechaAprob > '2021-01-01'