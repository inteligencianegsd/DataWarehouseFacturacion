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
	f.iva,
	f.total_iva ,
	f.total,
	f.codven,
	f.emision
FROM security_data.facturas f
ORDER BY f.emision ASC
