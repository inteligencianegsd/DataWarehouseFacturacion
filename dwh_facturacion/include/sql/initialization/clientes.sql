SELECT
    -- id_codcli,
    TRIM(codcli) as codcli,
    nomcli,
    cif,
    fecha_act
FROM security_data.clientes
ORDER BY fecha_act ASC