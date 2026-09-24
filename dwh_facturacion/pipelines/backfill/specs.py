"""
Specs de reconciliacion por tabla, usadas por ReconciliationPipeline. Ver
reconciliation_pipeline.py para el porque de este mecanismo.

Cada fenix_key_set_query devuelve la clave + `fecha_ref` (fecha para agrupar en la
notificacion) y se limita con `:watermark` sobre la MISMA columna que usa el
incremental de esa tabla (ver get_last_transaction_date de cada entidad bronze):
fecha_hora en facturas, fecha_act en clientes/vendedores, id_sec en rencon, id_codasi
en enccon.

Las claves se normalizan igual que en el incremental de cada tabla (TRIM solo donde el
SQL incremental lo hace, p.ej. clientes; CleanSpecialCharacters donde el pipeline
incremental lo aplica, p.ej. codven), para que la diferencia contra Bronze no marque
como faltantes filas que ya existen.

Las filas con la columna del watermark en NULL tambien se revisan: el incremental
(`<col> > :max`) nunca las carga, asi que el backfill es el unico que puede traerlas.

Solo contabilidad (rencon, enccon) usa sync_deletes: los asientos eliminados en Fenix
tambien se quitan de Bronze, para que fact_cuentas quede igual al origen. Facturacion no
borra nada (sus exclusiones se manejan con features.facturas_excluidas).
"""
from dwh_facturacion.entities.bronze.broze_facturas_entity import BronzeFacturaEntity
from dwh_facturacion.entities.bronze.bronze_clientes_entity import BronzeClienteEntity
from dwh_facturacion.entities.bronze.broze_vendedores_entity import BronzeVendedoresEntity
from dwh_facturacion.entities.bronze.bronze_rencon_entity import BronzeRenconEntity
from dwh_facturacion.entities.bronze.bronze_enccon_entity import BronzeEnconEntity
from dwh_facturacion.pipelines.backfill.reconciliation_pipeline import ReconciliationSpec

FACTURAS_SPEC = ReconciliationSpec(
    name="facturas",
    fenix_key_set_query="""
        SELECT f.numfac, DATE(f.emision) AS fecha_ref
        FROM security_data.facturas f
        WHERE f.emision >= :cutoff
          AND (f.fecha_hora <= :watermark OR f.fecha_hora IS NULL)
    """,
    fenix_key_col="numfac",
    fenix_recover_query="""
        SELECT
            f.id_numfac,
            f.numfac,
            f.numdoc,
            f.cliente,
            f.numser,
            f.pedido,
            f.comen1,
            f.comen2,
            f.comen3,
            f.subtotal,
            f.desc0,
            f.total_iva,
            f.total,
            f.codven,
            f.emision,
            f.fecha_hora
        FROM security_data.facturas f
        WHERE f.numfac IN :numfac
    """,
    fenix_key_param="numfac",
    bronze_entity=BronzeFacturaEntity,
    bronze_key_col="numfac",
    bronze_window_col="emision",
    conflict_cols=("numfac",),
    update_cols=(
        "numdoc", "cliente", "numser", "pedido", "comen1", "comen2", "comen3",
        "subtotal", "desc0", "total_iva", "total", "codven", "emision", "fecha_hora",
    ),
    clean_special_chars_cols=("codven",),
)

CLIENTES_SPEC = ReconciliationSpec(
    name="clientes",
    fenix_key_set_query="""
        SELECT TRIM(codcli) AS codcli, DATE(fecha_act) AS fecha_ref
        FROM security_data.clientes
        WHERE (fecha_act >= :cutoff AND fecha_act <= :watermark)
           OR fecha_act IS NULL
    """,
    fenix_key_col="codcli",
    fenix_recover_query="""
        SELECT TRIM(codcli) AS codcli, nomcli, cif, fecha_act
        FROM security_data.clientes
        WHERE TRIM(codcli) IN :codcli
    """,
    fenix_key_param="codcli",
    bronze_entity=BronzeClienteEntity,
    bronze_key_col="codcli",
    bronze_window_col="fecha_act",
    conflict_cols=("codcli",),
    update_cols=("update_date", "nomcli", "cif", "fecha_act"),
)

VENDEDORES_SPEC = ReconciliationSpec(
    name="vendedores",
    fenix_key_set_query="""
        SELECT codven, DATE(fecha_act) AS fecha_ref
        FROM security_data.vendedores
        WHERE (fecha_act >= :cutoff AND fecha_act <= :watermark)
           OR fecha_act IS NULL
    """,
    fenix_key_col="codven",
    fenix_recover_query="""
        SELECT id_codven, codven, nomven, fecha_act
        FROM security_data.vendedores
        WHERE codven IN :codven
    """,
    fenix_key_param="codven",
    bronze_entity=BronzeVendedoresEntity,
    bronze_key_col="codven",
    bronze_window_col="fecha_act",
    conflict_cols=("codven",),
    update_cols=("update_date", "nomven", "fecha_act"),
    clean_special_chars_cols=("codven",),
)

RENCON_SPEC = ReconciliationSpec(
    name="rencon",
    fenix_key_set_query="""
        SELECT id_sec, fecasi AS fecha_ref
        FROM security_data.rencon
        WHERE fecasi >= :cutoff
          AND id_sec <= :watermark
    """,
    fenix_key_col="id_sec",
    fenix_recover_query="""
        SELECT id_sec, codcomp, codcta, importe, codasi, fecasi, origen
        FROM security_data.rencon
        WHERE id_sec IN :id_sec
    """,
    fenix_key_param="id_sec",
    bronze_entity=BronzeRenconEntity,
    bronze_key_col="id_sec",
    bronze_window_col="fecasi",
    conflict_cols=("id_sec",),
    update_cols=("codcomp", "codcta", "importe", "codasi", "fecasi", "origen"),
    sync_deletes=True,
)

ENCCON_SPEC = ReconciliationSpec(
    name="enccon",
    fenix_key_set_query="""
        SELECT id_codasi, fecasi AS fecha_ref
        FROM security_data.enccon
        WHERE fecasi >= :cutoff
          AND id_codasi <= :watermark
    """,
    fenix_key_col="id_codasi",
    fenix_recover_query="""
        SELECT id_codasi, codcomp, codasi, fecasi, fecha
        FROM security_data.enccon
        WHERE id_codasi IN :id_codasi
    """,
    fenix_key_param="id_codasi",
    bronze_entity=BronzeEnconEntity,
    bronze_key_col="id_codasi",
    bronze_window_col="fecasi",
    conflict_cols=("id_codasi",),
    update_cols=("codcomp", "codasi", "fecasi", "fecha"),
    sync_deletes=True,
)

ALL_SPECS = (FACTURAS_SPEC, CLIENTES_SPEC, VENDEDORES_SPEC, RENCON_SPEC, ENCCON_SPEC)
