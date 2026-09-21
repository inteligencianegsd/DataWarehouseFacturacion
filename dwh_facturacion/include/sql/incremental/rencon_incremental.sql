SELECT
    r.id_sec,
	r.codcomp,
	r.codcta,
	r.importe,
	r.codasi,
	r.fecasi,
	r.origen
FROM security_data.rencon r
WHERE r.id_sec > :max_incremental_date
ORDER BY r.id_sec ASC
