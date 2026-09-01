# Checklist de secretos y configuración

## Variables necesarias
- NODE_ENV=production (si el proyecto necesita entorno de producción)
- NPM_TOKEN (si se usa una registry privada)
- GITHUB_TOKEN (se gestiona automáticamente por GitHub)

## Requisitos previos
- El repositorio debe tener Dependabot o `npm ci` compatible.
- Debe existir `package.json` con scripts `lint`, `test` y `build` cuando aplique.
- La rama `main` o `master` debe estar protegida si se desea exigir validación antes del merge.

## Buenas prácticas
- No guardar secretos dentro del YAML.
- Usar secrets y variables de entorno desde GitHub.
- Verificar que los pasos opcionales (`lint`, `build`) existan antes de desplegar.
- Mantener un log claro para cada ejecución.