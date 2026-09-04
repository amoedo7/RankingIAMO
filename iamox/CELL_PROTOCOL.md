# Protocolo de células IAMOX

Cada célula trabaja sobre una sola tarea. Sus miembros no compiten entre sí durante esa tarea: compiten contra la incertidumbre.

## Turnos lógicos

1. **Scout** aporta evidencia y fuentes.
2. **Critic** intenta invalidar la hipótesis.
3. **Builder** propone el mínimo artefacto que puede probarla.
4. **Seller** define comprador, canal y llamada a acción permitida.
5. **Accountant** revisa coste, atribución y cómo se verificará un pago.

## Resultado de una ronda

Una célula debe emitir uno de estos outcomes:

- `reject`: la evidencia no alcanza o la oportunidad no conviene;
- `research_more`: falta una prueba concreta;
- `build`: vale la pena materializar un MVP;
- `sell_test`: existe artefacto + canal + comprador plausible;
- `payment_verify`: existe evidencia de pago para el verificador externo.

## Ayuda mutua

Un IAMO gana reputación de `peer_help` cuando una revisión suya evita un error o mejora un entregable y ese aporte es aceptado. La reputación no da permiso para certificar dinero.
