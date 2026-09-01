# GBP Review Risk Monitor

MVP para monitorizar reseñas de Google Business Profile y resumir qué comentarios requieren respuesta urgente.

## Qué incluye
- `gbp_monitor.py`: analiza un CSV de reseñas y genera un resumen ejecutivo.
- `sample_reviews.csv`: ejemplo de datos con reseñas, fecha, rating y texto.
- `dashboard.html`: salida HTML para compartir con un cliente o propietario de clínica.

## Cómo ejecutarlo
1. Ajusta `sample_reviews.csv` con tus reseñas reales.
2. Ejecuta:
   `python gbp_monitor.py sample_reviews.csv --out dashboard.html`
3. Abre `dashboard.html` en el navegador.

## Resultado esperado
- Recuento total de reseñas por periodo
- Rating medio
- Comentarios negativos y frases de riesgo
- Prioridad por urgencia de respuesta
- Recomendaciones rápidas para mejorar reputación local

Referencia de pago: RANK-IAMO504