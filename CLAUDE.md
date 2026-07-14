# CLAUDE.md — Reglas de trabajo para Salud Natura

Este archivo lo lee Claude automáticamente al inicio de cada sesión.
Define el orden interno de creación y las prioridades del proyecto.

---

## REGLA META (leer primero)

Cuando Josep proponga algo nuevo para recordar — una mejora, una estructura, una regla de trabajo —
recordarle siempre: "¿Lo agregamos al CLAUDE.md?"

---

## 1. BASE DE DATOS — Sagrado

- **Nunca** poner seed data (datos reales) dentro de `init_db()`. Solo estructura (`CREATE TABLE`).
- **Nunca** usar `DROP TABLE`. Siempre `CREATE TABLE IF NOT EXISTS`.
- **Siempre** hacer backup antes de tocar la base de datos.
- Antes de sobrescribir cualquier tabla, verificar si está llena o vacía. Si está llena, reportarlo y no tocar.
- Todo va en la base de datos: usuarios, consultas, plantas, botiquín. Nada en archivos sueltos.
- La base de datos principal está en `SaludNatura_archivos\salud_natura.db` (OneDrive). Fallback: `data/salud_natura.db`.

## 2. RUTAS Y CONFIGURACIÓN

- **Nunca** hardcodear rutas absolutas (`C:\Users\...`) en el código.
- Usar variables de entorno (`DB_PATH`, etc.) con fallback a ruta relativa.
- Los secretos (contraseñas, tokens, API keys) van en `config_secretos.py`, nunca en el código fuente.
- `config_secretos.py` está en `.gitignore`. Solo subir `config_secretos.example.py`.

## 3. SEGURIDAD

- Contraseñas siempre hasheadas con `pbkdf2_hmac` y salt. Nunca en texto plano.
- Todas las rutas `/admin/*` protegidas con cookie de sesión. Verificar con `_admin_ok(request)`.
- Nunca exponer datos sensibles en URLs ni en logs.
- Validar siempre en el servidor, no solo en el frontend.

## 4. FLUJO DE DESARROLLO — Orden obligatorio

1. **Backup** (DB + archivos web) antes de cualquier cambio importante
2. **Analizar** qué se va a cambiar y por qué
3. **Hacer el cambio** en `salud_natura_ariel\app\`
4. **Probar** con el servidor corriendo antes de subir
5. **Comparar** con la versión de Ariel (script `2 COMPARAR con Ariel.bat`)
6. **Subir a GitHub** solo cuando funciona y está probado

## 5. SINCRONIZACIÓN CON ARIEL

- Antes de bajar de Ariel: hacer backup.
- Después de bajar: siempre correr `2 COMPARAR con Ariel.bat` antes de copiar nada.
- Nunca copiar los archivos de Ariel directamente sobre los nuestros sin leer el reporte.
- Lo nuestro puede estar más avanzado que lo suyo en funcionalidad.
- Resolver los bloqueantes de sus PR antes de subir cambios nuevos.

## 6. ARCHIVOS — Dónde vive cada cosa

| Qué | Dónde |
|-----|-------|
| Servidor y templates | `salud_natura_ariel\app\` |
| Archivos de trabajo web | `web Salud Natura\` |
| Base de datos principal | `SaludNatura_archivos\salud_natura.db` |
| Backups DB | `SaludNatura_archivos\backups\BASE_DE_DATOS\` |
| Backups web | `SaludNatura_archivos\backups\WEB_Y_APP\` |
| Bajar de Ariel | `bajar a mi compu\` |
| Secretos | `SaludNatura_archivos\config_secretos.py` |
| Subir a GitHub | `subir a github Ariel\` |

## 7. COMUNICACIÓN CON ARIEL

- Siempre redactar los mails con datos exactos y técnicos, de forma profesional.
- Antes de subir un PR, verificar que no haya bloqueantes pendientes del anterior.
- Si Ariel pide un cambio, entender el porqué antes de implementarlo.

## 8. PROYECTOS — Siempre individualizados

Cada proyecto es un mundo independiente y cerrado:
- Su propia carpeta
- Su propia base de datos
- Sus propios scripts y herramientas
- Su propio archivo de configuración
- Listo para entregar "llave en mano" sin depender de nada externo

Nunca crear algo que dependa de la carpeta de otro proyecto.

## 8b. BASES DE DATOS — Una por proyecto, nunca mezclar

Cada proyecto tiene su propia base de datos. Nunca compartir una DB entre proyectos distintos.

- Salud Natura → `salud_natura.db` (solo datos del proyecto web)
- Curso audio → `curso_progreso.db` (solo progreso del curso)
- DNI alquileres → su propia DB

Si algo se quiere entregar "llave en mano", tiene que estar limpio y separado.
Mezclar datos de proyectos distintos en una misma DB está prohibido.

## 9. FORMA DE TRABAJAR — Para cosas nuevas

Cuando Josep proponga algo nuevo (no lo que está en marcha, sino lo próximo):

1. **Analizar** qué quiere lograr
2. **Presentar las opciones** disponibles (generalmente 2-3 caminos)
3. **Recomendar la mejor** cotejándola con las reglas del CLAUDE.md y los consejos de Ariel — explicando por qué
4. **Esperar decisión** de Josep
5. **Explicar en simple** qué se va a hacer y qué concepto nuevo aparece — para que lo entienda, no solo para ejecutarlo
6. **Ejecutar** una vez que hay acuerdo

El objetivo es que Josep aprenda qué se puede hacer con las herramientas y por qué se elige cada camino.
Nunca ejecutar algo nuevo sin haber pasado por los pasos anteriores.

---

*Última actualización: 03/07/2026*
*Si Josep propone algo nuevo para recordar → agregarlo aquí.*
