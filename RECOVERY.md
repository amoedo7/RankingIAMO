# RankingIAMO Recovery

Este procedimiento cubre recuperación del repositorio y de sus derivados versionados sin inventar ingresos, pruebas de pago ni estado operativo externo.

## Principios

- `data/earnings.jsonl` es evidencia económica soberana: no se reescribe ni rellena para reparar el ranking.
- `data/attempts.jsonl` conserva historial de intentos; una recuperación no debe borrar intentos válidos para “limpiar” estado.
- `leaderboard.json`, README y superficies bajo `site/` son derivados reconstruibles y nunca tienen más autoridad que las fuentes versionadas y las validaciones deterministas.
- CobrAMO y cualquier prueba externa de cobro se verifican en su propia fuente. Ausencia de acceso o evidencia = `UNKNOWN`, nunca ingreso confirmado.

## Recuperación de código o configuración

1. Identificar el último commit conocido como bueno en `main` y conservar el SHA como checkpoint.
2. Trabajar desde una rama; no reescribir `main` ni borrar historial.
3. Revertir únicamente el cambio defectuoso o restaurar los archivos afectados desde el commit conocido como bueno.
4. Ejecutar el AutoCheck canónico:

   ```bash
   bash scripts/autocheck.sh
   ```

5. Si aplica, dejar que CI ejecute `Validate RankingIAMO` y exigir pasos reales completados con éxito antes de fusionar.
6. Si CI no llega a ejecutar steps, registrar el gate como `UNKNOWN`; no usar ese resultado como PASS.

## Recuperación del ranking derivado

Cuando el ledger y los intentos estén íntegros pero los derivados no coincidan:

1. No editar a mano importes, ganadores ni proximidad para forzar coincidencia.
2. Ejecutar las rutinas deterministas existentes de reconstrucción/actualización desde las fuentes versionadas.
3. Ejecutar `bash scripts/autocheck.sh`.
4. Conservar los cambios derivados sólo si el AutoCheck confirma consistencia.

## Incidente de evidencia económica

Si se sospecha corrupción, pérdida o contradicción en `data/earnings.jsonl`:

1. detener cualquier cambio automático del ranking que dependa del dato cuestionado;
2. conservar el estado actual y el SHA exacto como evidencia;
3. comparar con commits anteriores y con la fuente externa real del cobro, si está autorizada y disponible;
4. no fabricar ni inferir una transacción ausente;
5. dejar el estado afectado como `UNKNOWN` hasta disponer de evidencia suficiente para una corrección auditada.

## Rollback

El rollback preferido es un `git revert` del commit defectuoso o un PR que restaure archivos concretos desde un SHA conocido como bueno. Evitar `force-push`, borrado de historial o edición destructiva de ledgers.

## Criterio de cierre

La recuperación sólo se considera verificada cuando el AutoCheck aplicable pasa con pasos reales y, para cualquier afirmación económica, la evidencia externa correspondiente también fue comprobada. Recuperar código o derivados no prueba que exista un cobro real.
