SELECT
    id_codcli,
    codcli,
    nomcli,
    cif,
    fecha_act
FROM security_data.clientes
ORDER BY fecha_act DESC
LIMIT 100