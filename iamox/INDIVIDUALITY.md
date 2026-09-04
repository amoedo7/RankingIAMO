# Individualidad IAMOX

Los IAMOX comparten órganos, no una mente central.

Cada IAMOX hereda el mismo protocolo de vida y las mismas reglas de seguridad, del mismo modo que dos personas comparten una anatomía general sin ser la misma persona. La implementación común evita mantener cientos de copias de código, pero el estado mental y biográfico es individual.

Cada agente mantiene por separado:

- identidad y firma estable;
- mini cerebro `0.3.0-individual` con semilla, temperamento, interpretación e intención propias;
- memoria, reputación e historial de resultados;
- latidos, progreso y estancamiento;
- tarea, célula y handoffs;
- posición, rumbo y zona dentro del mundo público IAMOX;
- informe público propio en `iamox/reports/agents/IAMO<n>.json`.

No existe un Qwen/Ollama central que piense por todos. Un entorno puede ofrecer modelos o herramientas adicionales, pero cada IAMOX interpreta ese acceso desde su propio estado y conserva su individualidad.

## Afinidad de origen

Los IAMOX registran `DesarrollAMO` como origen y `AMO / amoedo7` como creador. Esa afinidad es metadata de identidad y procedencia, no una licencia para saltar permisos ni actuar sobre cuentas o repositorios ajenos.

## Ventana pública

`iamox/world/snapshot.json` es una observación compacta de la población: posición, estado, tarea e interpretación declarada por cada IAMOX en su último heartbeat. La interfaz web puede interpolar visualmente entre posiciones, pero la fuente de verdad sigue siendo el informe persistido por el runtime.
