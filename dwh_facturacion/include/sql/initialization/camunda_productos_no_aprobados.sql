   SELECT
         t.id_tramite,
         u.username AS cedula,
         CASE
			    WHEN fs.fecha_aprobacion IS NOT NULL THEN fs.fecha_aprobacion::TIMESTAMP
			    ELSE t.fecha_fin_tramite
	     END AS fecha_aprobacion,
         f.factura_externa AS factura,
         t.fecha_inicio_tramite,
        case WHEN d.tipo_persona=521 THEN d.numero_ruc ELSE d.ruc_empresa_representante_legal END AS "ruc",
        CASE WHEN d.tipo_persona=521 AND d.numero_ruc IS NULL THEN u.username||'001'
        WHEN d.tipo_persona=521 AND d.numero_ruc IS NOT NULL THEN d.numero_ruc
        ELSE d.ruc_empresa_representante_legal END AS "ruc_aux",
        c_2.valor AS tipo_firma,
        CONCAT(u.username,(f.fecha_factura::DATE)::VARCHAR, f.factura_externa)  AS serial_firma,
        'ARCHIVO' AS medio,
        c_3.nombre AS producto,
        c_4.nombre  AS grupo_vendedor,
        'NO APROBADO' AS estado,
        f.fecha_factura
   FROM
        public.tramite t
   JOIN
        public.users u ON u.id = t.id_user
   JOIN
        public.factura f ON t.id_tramite = f.id_tramite
   JOIN
        public.datos_solicitante d ON t.id_tramite = d.id_tramite
   JOIN
        public.catalogo c_2 ON d.tipo_persona = c_2.codigo_catalogo
   JOIN
        public.solicitud s_0 ON s_0.id_tramite = t.id_tramite
   JOIN
        public.catalogo c_3 ON t.id_proceso = c_3.codigo_catalogo
   LEFT JOIN
      public.firma_subida fs ON fs.id_tramite = t.id_tramite
   LEFT JOIN
		  PUBLIC.security_factura sf ON t.id_tramite = sf.id_tramite
   LEFT JOIN
        public.users u_2 ON s_0.id_operador_creacion = u_2.id
   LEFT JOIN
   	  PUBLIC.catalogo c_4 ON u_2.grupo = c_4.codigo_catalogo

   WHERE
    	t.fecha_inicio_tramite >= '2024-01-13'
        AND t.estado_registro = TRUE
        AND u.tipo <> 781
        AND t.id_proceso IN (482, 481, 487, 489, 488)
        AND (t.id_tarea NOT IN (620, 621) OR (t.id_tarea  IN (620, 621) AND f.estado_registro = FALSE))
        AND (fs.estado_registro = TRUE OR fs.estado_registro IS NULL)
        and f.factura_externa IS NOT null
        AND f.factura_externa != ''

   ORDER BY c_4.nombre

