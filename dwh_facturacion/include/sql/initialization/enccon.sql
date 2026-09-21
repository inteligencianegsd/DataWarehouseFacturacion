SELECT
    e.id_codasi,
	e.codcomp,
	e.codasi,
	e.fecasi,
	e.fecha
FROM security_data.enccon e
WHERE e.fecasi >= '2024-01-01'
ORDER BY e.fecha ASC
