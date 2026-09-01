# Checklist de QA del feed

## 1) Titulos y variantes
- [ ] Revisar que cada Title sea único y no duplicado por variante.
- [ ] Validar que Variant Title no repita el nombre del producto sin contexto.
- [ ] Confirmar que la estructura del nombre no supere la longitud recomendada.

## 2) Identificadores
- [ ] Comprobar GTIN/MPN para cada SKU relevante.
- [ ] Corregir valores faltantes o inconsistentes.
- [ ] Eliminar códigos duplicados de variantes.

## 3) Imágenes y URLs
- [ ] Revisar Image Src y Image Alt.
- [ ] Comprobar URLs rotas, redirects o dominios no esperados.
- [ ] Confirmar que el producto visible coincide con el feed.

## 4) Exportación
- [ ] Verificar que el CSV exportado no contiene filas vacías.
- [ ] Confirmar que no hay handles duplicados ni columnas sin formato.
- [ ] Validar que los cambios se reflejan en la previsualización de Merchant Center.

## 5) Entrega final
- [ ] Compartir versión corregida del CSV.
- [ ] Dejar resumen corto de cambios con ejemplos.
- [ ] Confirmar la referencia de pago RANK-IAMO505.