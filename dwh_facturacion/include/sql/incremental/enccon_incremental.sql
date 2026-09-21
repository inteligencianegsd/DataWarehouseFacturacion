SELECT
    e.id_codasi,
	e.codcomp,
	e.codasi,
	e.fecasi,
	e.fecha
FROM security_data.enccon e
WHERE e.fecha > :max_incremental_date
ORDER BY e.fecha ASC
