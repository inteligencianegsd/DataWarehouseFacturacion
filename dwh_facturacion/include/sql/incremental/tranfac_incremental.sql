SELECT
    id_tranfac,
    unico,
    numfac,
    codart,
    cantidad_d,
    precio,
    desct,
    iva
FROM security_data.tranfac
WHERE id_tranfac > :max_incremental_id
ORDER BY id_tranfac ASC