
######################################################################
# Gateway WS<->WS par conectar el ESP32 que gobierna el aeropéndulo al 
# backend del sistema VirtyRemLab-
# El servicio lo
# Autor: Diego García
######################################################################

import asyncio
import socketio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import websockets
import struct
import json
import time
import subprocess
import base64




# Crear aplicación FastAPI
app = FastAPI()



#####################################################################################
## Gestión de la conexión con el ESP32
#####################################################################################

# Guardar el estado del ESP32 (si necesitas enviarle datos)
esp32_websockets = set()

# Handler de mensajes WebSocket
async def ws_esp32_handler(websocket):
    print("ESP32 conectado")
    esp32_websockets.add(websocket)
    try:
        async for message in websocket:
            if isinstance(message,bytes):
                dataBloc = struct.unpack("<ff",message)
                print(f"[ESP32] → {time.time()}:{dataBloc}")
               
    except websockets.exceptions.ConnectionClosedError:
        print("ESP32 desconectado")
    finally:
        esp32_websockets.remove(websocket)




async def serve_ws():
    async with websockets.serve(ws_esp32_handler, "0.0.0.0", 8765) as server:
        print("Servidor WebSocket corriendo en puerto 8765")
        await server.serve_forever()  # Nunca termina

# Iniciar WebSocket Server como tarea background
@app.on_event("startup")
async def start_ws_server():
    asyncio.create_task(serve_ws())


