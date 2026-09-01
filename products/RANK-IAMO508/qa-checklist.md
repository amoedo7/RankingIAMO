# Checklist QA para feeds de Google Shopping y Meta

## Revisión crítica
- [ ] Títulos no duplicados ni genéricos
- [ ] Variantes con nombres consistentes
- [ ] URLs y handles alineados con el producto correcto
- [ ] GTIN/MPN presentes cuando aplica
- [ ] Imágenes y variantes registradas correctamente
- [ ] Precios y stock coherentes con Shopify
- [ ] Descripciones con texto limpio y sin caracteres raros
- [ ] Productos activos y visibles en el feed

## Señales de alerta
- [ ] Títulos con nombres incompletos o importados de variantes
- [ ] GTIN/MPN faltantes en productos de marca o multiplexados
- [ ] URLs que no coinciden con la página real
- [ ] Variantes duplicadas por color/talla
- [ ] Producto rechazado por imagen inválida, precio o stock

## Validación final
1. Exportar feed desde Shopify.
2. Revisar filas con errores críticos.
3. Corregir en CSV o en la base del producto.
4. Subir feed nuevo.
5. Confirmar que no aparecen errores bloqueantes en Google Merchant Center y Meta Catalog.