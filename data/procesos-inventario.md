# Manual de gestión de inventario

## Proceso de recepción de mercancía
Cuando llega un pedido al almacén, el operario debe escanear cada unidad
con el lector RFID antes de confirmar la recepción en el sistema. Si hay
discrepancias entre el albarán y las unidades recibidas, se abre una
incidencia en el módulo de proveedores.

## Sincronización de stock entre tiendas
El sistema sincroniza el stock de todas las tiendas cada 15 minutos mediante
un job programado. Si una tienda detecta rotura de stock, puede solicitar
traspaso desde otra tienda con excedente a través del panel de operaciones.

## Proceso de inventario físico
El inventario físico se realiza trimestralmente. Durante el proceso, las
tiendas afectadas quedan en modo lectura — pueden consultar stock pero no
realizar movimientos hasta que el inventario esté cerrado y validado.

## Gestión de devoluciones
Las devoluciones de cliente se procesan en tienda. El artículo devuelto
vuelve al stock disponible si pasa el control de calidad, o se marca como
merma si está dañado. Ambos casos actualizan el stock en tiempo real.