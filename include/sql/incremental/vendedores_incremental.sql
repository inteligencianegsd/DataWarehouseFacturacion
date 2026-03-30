SELECT
    id_codven,
    codven,
    nomven,
    fecha_act
FROM security_data.vendedores
WHERE fecha_act > :max_incremental_date
ORDER BY fecha_act ASC