SELECT
    id_tranfac,
    unico,
    numfac,
    codart,
    cantidad_d,
    precio,
    desct
FROM security_data.tranfac
ORDER BY id_tranfac DESC
LIMIT 100