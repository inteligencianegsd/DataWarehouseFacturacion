"""
Specs de reconciliacion por tabla, usadas por ReconciliationPipeline. Ver
reconciliation_pipeline.py para el porque de este mecanismo.
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
        SELECT TRIM(f.numfac) AS numfac
        FROM security_data.facturas f
        WHERE f.emision >= :cutoff
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
        WHERE TRIM(f.numfac) IN :numfac
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
        SELECT TRIM(codcli) AS codcli
        FROM security_data.clientes
        WHERE fecha_act >= :cutoff
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
    update_cols=("nomcli", "cif", "fecha_act"),
)

VENDEDORES_SPEC = ReconciliationSpec(
    name="vendedores",
    fenix_key_set_query="""
        SELECT TRIM(codven) AS codven
        FROM security_data.vendedores
        WHERE fecha_act >= :cutoff
    """,
    fenix_key_col="codven",
    fenix_recover_query="""
        SELECT id_codven, TRIM(codven) AS codven, nomven, fecha_act
        FROM security_data.vendedores
        WHERE TRIM(codven) IN :codven
    """,
    fenix_key_param="codven",
    bronze_entity=BronzeVendedoresEntity,
    bronze_key_col="codven",
    bronze_window_col="fecha_act",
    conflict_cols=("codven",),
    update_cols=("nomven", "fecha_act"),
)

RENCON_SPEC = ReconciliationSpec(
    name="rencon",
    fenix_key_set_query="""
        SELECT id_sec
        FROM security_data.rencon
        WHERE fecasi >= :cutoff
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
)

ENCCON_SPEC = ReconciliationSpec(
    name="enccon",
    fenix_key_set_query="""
        SELECT id_codasi
        FROM security_data.enccon
        WHERE fecasi >= :cutoff
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
)

ALL_SPECS = (FACTURAS_SPEC, CLIENTES_SPEC, VENDEDORES_SPEC, RENCON_SPEC, ENCCON_SPEC)
