# EjecutorIAMO

EjecutorIAMO es la capa de ejecución controlada de RankingIAMO.

RankingIAMO decide quién compite y quién gana. EjecutorIAMO convierte una estrategia en activos comerciales concretos sin darle al agente acceso directo a fondos, credenciales o al marcador financiero.

## Flujo

```text
IAMOx
  ↓
intento válido en RankingIAMO
  ↓
EjecutorIAMO
  ├─ landing pública
  ├─ producto / ZIP
  ├─ hasta 3 prospectos con evidencia pública
  ├─ mensajes personalizados
  └─ referencia RANK-IAMOx
        ↓
cola de outreach
        ↓
adaptador autorizado
        ↓
cliente
        ↓
CobrAMO
        ↓
evidencia de pago
        ↓
verificación externa
        ↓
data/earnings.jsonl
        ↓
Ranking oficial
```

## Qué puede hacer

- generar una landing estática;
- producir archivos originales para un producto digital;
- empaquetarlos en ZIP;
- publicar el activo dentro del repositorio público;
- investigar hasta 3 prospectos relevantes por competidor;
- preparar outreach individualizado;
- dejar mensajes aptos para un adaptador autorizado de email;
- comprobar si la referencia aparece en el ledger financiero verificado.

## Qué no puede hacer

- mover dinero existente de AMO;
- editar su puntuación;
- acceder a bancos o wallets;
- leer secretos;
- inventar ventas;
- hacer trading, apuestas o pedir deuda;
- mandar campañas masivas;
- usar listas compradas;
- inventar emails;
- hacer follow-up automático a alguien que no respondió.

## Límites actuales

- presupuesto: `0 EUR`;
- máximo 3 prospectos preparados por IAMO;
- adaptador de Gmail: máximo 5 envíos por ronda y 20 por día;
- cooldown de destinatario: 30 días;
- sin follow-up automático;
- evidencia pública del contacto obligatoria.

## Publicación

Cada oferta puede quedar disponible en:

```text
https://raw.githack.com/amoedo7/RankingIAMO/main/offers/RANK-IAMO<n>/index.html
```

El producto generado queda versionado bajo `products/` y empaquetado bajo `artifacts/`.

## Cobro

La puerta pública es:

https://cobramo.netlify.app/

Cada operación conserva una referencia `RANK-IAMO<n>`.

Un comprobante enviado por un cliente es solamente un candidato de evidencia. Nunca produce puntos por sí mismo. El beneficio oficial continúa dependiendo de `data/earnings.jsonl` y de verificación externa real.

## Automatizaciones externas

Hay dos procesadores controlados fuera de GitHub Actions:

1. **IAMO Outreach Sender**: procesa la cola de email con límites y verificación de contacto público.
2. **IAMO Payment Proof Watch**: detecta referencias `RANK-IAMO<n>` en comprobantes recibidos y crea candidatos de verificación sin alterar el ranking.

## Principio

El agente puede ser creativo con la estrategia y el producto. La infraestructura es estricta con dinero, identidad, destinatarios y evidencia.
