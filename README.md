# Black Dog - Sistema de Transferencias

Aplicación web para cargar archivos `.txt` con pedidos y generar transferencias internas en Odoo automáticamente.

## Funcionalidades
- Login de usuario (admin y operaciones)
- Subida de múltiples archivos `.txt`
- Procesamiento uno a uno con logs
- Logs detallados por archivo
- Interfaz moderna con logo de Black Dog
- Preparado para deployment en Railway.app
- Soporte para dominio personalizado: `transferencias.blackdogpanama.com`

## Despliegue en Railway
1. Sube este proyecto a GitHub.
2. En Railway, crea un nuevo proyecto y selecciona tu repo.
3. Agrega variables de entorno desde `.env.example` en **Settings → Variables**.
4. Railway usará `Procfile` para desplegar automáticamente.
5. Conecta tu dominio en **Settings → Domains** con un registro CNAME.

## Uso local
1. Renombra `.env.example` a `.env` y ajusta valores.
2. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
3. Corre local:
   ```
   flask run --host=0.0.0.0 --port=5000
   ```
