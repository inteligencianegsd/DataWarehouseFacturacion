SELECT
    -- id_codcli,
    TRIM(codcli) as codcli,
    nomcli,
    cif,
    fecha_act
FROM security_data.clientes
WHERE fecha_act > :max_incremental_date
ORDER BY fecha_act ASC