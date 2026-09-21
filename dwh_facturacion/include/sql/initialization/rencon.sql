SELECT
    r.id_sec,
	r.codcomp,
	r.codcta,
	r.importe,
	r.codasi,
	r.fecasi,
	r.origen
FROM security_data.rencon r
WHERE r.fecasi >= '2024-01-01'
ORDER BY r.id_sec ASC
