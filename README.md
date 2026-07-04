# Servidor de dibujo SSM — Deploy en Railway

## Archivos necesarios en este proyecto

```
main.py                ← servidor Flask (este archivo)
build_estilo_ssm.py    ← script de dibujo (descargado de la conversación)
requirements.txt       ← dependencias Python
nixpacks.toml          ← instrucción para instalar Graphviz en Railway
```

## Pasos para deployar en Railway

1. Entra a https://railway.app y crea cuenta con GitHub (gratis).

2. Crea un nuevo proyecto:
   - New Project → Empty Project → Add Service → GitHub Repo
   - O: New Project → Deploy from template → seleccionar "Empty"

3. Sube los 4 archivos a un repositorio de GitHub y conéctalo a Railway.
   También puedes usar Railway CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   railway init
   railway up
   ```

4. Railway detecta nixpacks.toml y requirements.txt automáticamente.
   El build instala Graphviz, Cairo y las dependencias Python.

5. Una vez deployado, Railway te da una URL pública:
   ```
   https://tu-proyecto-nombre.railway.app
   ```

6. Verifica que funciona:
   ```bash
   curl https://tu-proyecto-nombre.railway.app/health
   # Respuesta esperada: {"status": "ok"}
   ```

## Configurar la URL en n8n

En n8n cloud, ve a:
Settings → Environment Variables → Agregar variable:

```
Nombre:  RAILWAY_URL
Valor:   https://tu-proyecto-nombre.railway.app
```

Esa variable es la que usan los nodos HTTP Request del flujo para saber
dónde llamar al servidor de dibujo.

## Probar el servidor manualmente

```bash
curl -X POST https://tu-proyecto-nombre.railway.app/generar \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Sistema de prueba",
    "output": "Sistema mejorado",
    "actividades": [
      {"id": "a1", "texto": "Detectar el problema"},
      {"id": "a2", "texto": "Analizar las causas"},
      {"id": "a3", "texto": "Proponer soluciones"},
      {"id": "a4", "texto": "Implementar cambios"},
      {"id": "a5", "texto": "Evaluar resultados"}
    ],
    "flechas": [["a1","a2"],["a2","a3"],["a3","a4"],["a4","a5"]]
  }'
```

Respuesta esperada:
```json
{
  "data": "<base64 del PNG>",
  "svg": "<contenido SVG>",
  "actividades": 5,
  "flechas": 4
}
```

## Plan gratuito de Railway

El plan Hobby gratuito incluye:
- $5 USD de crédito mensual (suficiente para este uso)
- El servidor puede dormir si no recibe requests (se despierta automáticamente)
- Si el servidor está dormido, el primer request puede tardar ~10s extra

Para evitar que duerma, configura un cron en n8n que haga un GET a /health
cada 14 minutos.
