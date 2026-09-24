SELECT
    e.id_codasi,
	e.codcomp,
	e.codasi,
	e.fecasi,
	e.fecha
FROM security_data.enccon e
WHERE e.id_codasi > :max_incremental_date
ORDER BY e.id_codasi ASC
