# Sin Nombre v3

Interfaz negra y amarilla, conversaciones temporales, fotos, envío con Enter y desplazamiento automático al mensaje más reciente.

## Instalación limpia en Windows

```powershell
cd sin-nombre-v3
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abre `http://127.0.0.1:8000`. Desde otro equipo de la red usa `http://IP-DE-TU-PC:8000`.

## Si reemplazas archivos de una versión anterior

No es necesario borrar `sin_nombre.db`: esta versión agrega automáticamente las columnas `image` que falten en SQLite. Haz una copia de seguridad antes de cualquier cambio importante.

## Controles del chat

- Enter: enviar.
- Shift + Enter: nueva línea.
- La conversación abre y vuelve automáticamente al mensaje más reciente.
- El botón `+` adjunta JPG, PNG o WEBP de hasta 5 MB.
- La duración puede ser de 20 minutos a 24 horas.

## Producción

Las fotos se guardan en `uploads/` durante desarrollo. Antes de Render deben moverse a Supabase Storage o almacenamiento persistente. También faltan moderación de imágenes, eliminación de EXIF, rate limiting y panel de reportes antes de abrirlo al público.
