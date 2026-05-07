def build_connection_url(config):
    engine = config.get('engine', 'postgresql')
    driver = config.get('driver', 'psycopg2')
    user = config['user']
    password = config['password']
    host = config['host']
    port = config['port']
    db = config.get('database', '')
    odbc_driver = config.get('odbc_driver')  # <- este lo leerá SOLO SQL Server

    if not engine or not driver:
        raise ValueError("Faltan parámetros obligatorios: 'engine' o 'driver'")

    # Construcción base
    url = f"{engine}+{driver}://{user}:{password}@{host}:{port}"

    # ---- CASO ESPECIAL SQL SERVER ----
    if engine.lower() == "mssql":
        if not odbc_driver:
            raise ValueError("Para SQL Server debes definir DB_ODBC_DRIVER_LATINUM en tu .env")

        # Reemplaza espacios por "+" para URL
        odbc_driver_encoded = odbc_driver.replace(" ", "+")

        # Agregar parámetros obligatorio del driver
        return f"{url}/{db}?driver={odbc_driver_encoded}&TrustServerCertificate=yes"

    # ---- TODOS LOS OTROS MOTORES ----
    return f"{url}/{db}" if db else url
