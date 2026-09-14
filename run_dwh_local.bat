@echo off
setlocal

REM =====================================================================
REM Replica local del DAG dwh_facturacion_dag (Airflow) para correr
REM manualmente cuando QUANTA (172.24.54.100) no esta disponible.
REM Destino: base local_backup (127.0.0.1:5432 / contabilidad_backup_20260910)
REM =====================================================================

cd /d "%~dp0"
set PYTHONPATH=%~dp0

set LOGDIR=%~dp0logs_local_run
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set TS=%DT:~0,8%_%DT:~8,6%
set LOGFILE=%LOGDIR%\run_%TS%.log

echo ===================================================== > "%LOGFILE%"
echo DWH Facturacion - corrida LOCAL - %DATE% %TIME% >> "%LOGFILE%"
echo ===================================================== >> "%LOGFILE%"

echo [1/3] Ejecutando tareas Python (features + bronze) contra LOCAL...
python "%~dp0run_dwh_local.py" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: fallo una de las tareas Python. Revisa "%LOGFILE%"
    goto :fin_error
)

echo [2/3] Ejecutando dbt run --target local_backup...
dbt run --target local_backup --project-dir "%~dp0dwh_facturacion_dbt" --profiles-dir "%USERPROFILE%\.dbt" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: fallo dbt run. Revisa "%LOGFILE%"
    goto :fin_error
)

echo [3/3] Ejecutando dbt test --target local_backup...
dbt test --target local_backup --exclude resource_type:seed --project-dir "%~dp0dwh_facturacion_dbt" --profiles-dir "%USERPROFILE%\.dbt" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo.
    echo ADVERTENCIA: dbt test reporto fallos/warnings. Revisa "%LOGFILE%"
    goto :fin_warning
)

echo.
echo =====================================================
echo   CORRIDA LOCAL COMPLETADA OK
echo   Log: %LOGFILE%
echo =====================================================
goto :eof

:fin_warning
echo.
echo =====================================================
echo   CORRIDA LOCAL COMPLETADA CON ADVERTENCIAS (ver log)
echo   Log: %LOGFILE%
echo =====================================================
goto :eof

:fin_error
echo.
echo =====================================================
echo   CORRIDA LOCAL FALLO - revisar log antes de reintentar
echo   Log: %LOGFILE%
echo =====================================================
exit /b 1
