# Gestión de RFID y etiquetado

## Etiquetado de producto

Todos los artículos reciben una etiqueta RFID en el momento de la recepción
en el centro logístico, antes de su distribución a tienda. Cada etiqueta
contiene un identificador único (EPC) vinculado a la referencia de producto,
talla, color y lote de fabricación.

Las etiquetas RFID se colocan en una ubicación estándar según la categoría
de producto (cuello para prendas superiores, cinturilla para pantalones,
suela o caja para calzado), para que la lectura sea consistente en los
arcos de seguridad y en los lectores de mano.

## Lectura en recepción de tienda

Cuando llega mercancía nueva a tienda, el encargado debe pasar el lector
RFID portátil por la totalidad de la caja o palet recibido, sin necesidad
de abrir cada bolsa individual. El sistema compara automáticamente las
unidades leídas contra el albarán de envío y marca discrepancias si el
número de unidades no coincide.

Una discrepancia entre lo leído y lo esperado en el albarán debe resolverse
antes de dar por finalizada la recepción. Si la diferencia persiste tras un
segundo conteo manual, se abre una incidencia de logística con el número de
albarán y la referencia afectada.

## Inventario cíclico con RFID

Cada tienda realiza un inventario cíclico semanal sobre un subconjunto de
categorías (rotación por categoría, no inventario completo), usando el
lector RFID de mano para contar unidades en sala y en almacén trasero en
cuestión de minutos, en lugar de un conteo manual artículo por artículo.

Este inventario cíclico **no sustituye** al inventario físico trimestral
completo, que sigue siendo obligatorio y se realiza con la tienda en modo
lectura, sin movimientos de stock durante el proceso.

## Discrepancias de inventario

Cuando el conteo RFID de un inventario cíclico difiere del stock teórico en
el sistema en más de un 3% sobre el total de unidades de esa categoría, se
marca automáticamente para revisión por el equipo de pérdida desconocida
(shrinkage). Diferencias por debajo de ese umbral se consideran dentro de
tolerancia operativa normal y no generan alerta.

Las causas más habituales de discrepancia son: etiquetas dañadas o
arrancadas, ventas no registradas correctamente en el POS, y traspasos
entre tiendas no confirmados en el sistema por el receptor.

## Desactivación de la etiqueta en venta

En el momento del cobro en caja, el sistema POS desactiva automáticamente
la señal RFID de los artículos vendidos, de forma que dejan de contar como
stock disponible y no activan la alarma de los arcos de seguridad a la
salida. Si un cliente sale de tienda y la alarma salta, el protocolo indica
comprobar primero si el artículo fue correctamente desactivado en el ticket
antes de asumir un posible hurto.

## Vida útil y sustitución de etiquetas

Las etiquetas RFID pasivas usadas en producto textil no requieren batería y
tienen una vida útil indefinida mientras no se dañen físicamente. En
calzado y accesorios de piel, las etiquetas se integran en una funda
extraíble que debe retirarse en el momento de la venta, a diferencia del
textil, donde algunas categorías usan etiquetas cosidas que se desactivan
pero no se retiran físicamente.