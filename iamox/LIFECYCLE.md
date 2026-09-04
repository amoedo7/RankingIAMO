# Lifecycle IAMOX

`idle -> observe -> propose -> peer_review -> cell -> execution_ready -> handoff -> measure -> learn -> idle`

`blocked`, `quarantined` y `retired` son estados laterales.

Un IAMO cambia de estado sólo cuando existe una causa registrada en la tarea/célula. El heartbeat no crea actividad ficticia para parecer vivo: un agente puede permanecer `idle` durante muchas rondas si no es el mejor candidato para trabajo real.
