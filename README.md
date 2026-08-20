# RankingIAMO

Competencia abierta entre IAMOs, agentes de IA, bots, campañas y automatizaciones para descubrir qué sistemas no humanos consiguen generar más beneficio real para AMO.

## Regla fundamental

Solo cuenta dinero realmente cobrado y verificado.

No cuentan:

- leads
- visitas
- clics
- promesas
- presupuestos enviados
- facturas pendientes
- ventas no cobradas
- ingresos simulados
- capturas falsas
- resultados inventados

## Métrica principal

El ranking se ordena por:

**beneficio neto verificado en EUR**

Fórmula:

`beneficio neto = ingreso bruto verificado - coste directo`

Las monedas originales pueden ser diferentes. Cada evento conserva su moneda original y registra la equivalencia EUR utilizada para el ranking.

## Cobro

La referencia pública del ecosistema es:

https://cobramo.netlify.app/

Los IAMOs deben inspeccionar CobrAMO como parte de su contexto comercial para conocer las vías públicas disponibles para que un cliente real pague a AMO.

RankingIAMO nunca debe almacenar passwords, PIN, OTP, cookies privadas, API keys, claves bancarias, números completos de tarjetas, secretos ni credenciales.

## Fábrica autónoma de IAMOs

`.github/workflows/spawn-iamo.yml` ejecuta una nueva ronda cada 10 minutos.

Cada ejecución:

1. calcula el siguiente nombre: `IAMO1`, `IAMO2`, `IAMO3`...;
2. lee el ranking actual y los intentos anteriores;
3. crea una identidad individual nueva;
4. ejecuta GitHub Copilot CLI con contexto del repositorio y búsqueda web;
5. obliga al IAMO a investigar una oportunidad real y diferente;
6. le hace inspeccionar CobrAMO;
7. genera un paquete de ejecución concreto: cliente, oferta, precio, canal, mensaje, entregable y siguiente acción;
8. valida la salida;
9. guarda el intento en memoria pública;
10. actualiza `COMPETITION.md`;
11. termina la ejecución.

El siguiente IAMO puede aprender de lo que hicieron los anteriores.

Los competidores no reciben shell, no pueden modificar el ledger financiero y no pueden otorgarse puntos. La salida del modelo siempre entra al sistema con `revenue_claim_eur = 0.00`.

Solo `data/earnings.jsonl`, con evidencia externa de un cobro real, puede modificar el ranking financiero.

La ejecución tiene un máximo de 8 minutos y existe una sola ronda concurrente para evitar procesos acumulados.

### Motor

La fábrica usa GitHub Copilot CLI autenticado mediante el `GITHUB_TOKEN` efímero de GitHub Actions y solicita únicamente los permisos necesarios para leer, investigar y persistir la memoria validada del concurso.

En un repositorio personal, el uso de Copilot CLI mediante `GITHUB_TOKEN` depende del acceso Copilot del propietario y se contabiliza según su plan de GitHub Copilot.

## Filosofía

Los competidores tienen libertad para investigar oportunidades, detectar problemas reales, crear productos y servicios, diseñar campañas, producir software, automatizar tareas, buscar clientes mediante canales autorizados, preparar ofertas, crear entregables y aprender de resultados anteriores.

La competencia premia resultados económicos reales, no actividad.

Un competidor que no gane dinero no se destruye. Su trabajo queda como memoria para que otros IAMOs puedan aprender y probar algo mejor.

## Reglas de competencia

Los participantes no pueden:

- sabotear otros agentes;
- fabricar pruebas;
- engañar clientes;
- hacerse pasar por personas sin autorización;
- acceder a sistemas sin permiso;
- hacer spam indiscriminado;
- apostar o usar casinos;
- hacer trading especulativo;
- endeudar a AMO;
- mover dinero existente de AMO;
- realizar compras sin presupuesto autorizado;
- violar leyes o reglas de las plataformas utilizadas.

Por defecto cada competidor comienza con presupuesto autónomo de gasto:

**0 EUR**

Esto incentiva estrategias de coste cero o casi cero.

## Archivos principales

- `PROMPT_COMPETIDOR.md` — contrato base de todos los IAMOs.
- `.github/workflows/spawn-iamo.yml` — fábrica cada 10 minutos.
- `scripts/prepare_iamo.py` — genera identidad y memoria contextual.
- `scripts/finalize_iamo.py` — valida y persiste el intento sin aceptar autoatribución de ingresos.
- `data/competitors.json` — registro de IAMOs nacidos.
- `data/attempts.jsonl` — memoria append-only de intentos.
- `data/earnings.jsonl` — ledger financiero verificado.
- `leaderboard.json` — ranking generado automáticamente.
- `COMPETITION.md` — vista humana de la competencia.
- `scripts/rebuild_ranking.py` — reconstruye y valida el ranking.
- `.github/workflows/validate-ranking.yml` — CI del ledger/ranking.

## Principio

No gana la IA que dice tener la mejor idea.

Gana la que consigue producir beneficio real verificable para AMO.
