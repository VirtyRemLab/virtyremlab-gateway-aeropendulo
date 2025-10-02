
######################################################################
# Gateway WS<->WS par conectar el ESP32 que gobierna el aeropéndulo al 
# backend del sistema VirtyRemLab-
# El servicio lo
# Autor: Diego García
######################################################################

import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import websockets
import struct
import json
import time
from pydantic import BaseModel



PORT = 8765

# Crear aplicación FastAPI
app = FastAPI()


# Request body
class Item(BaseModel):
    Tm: float


# Método post para cambiar el periodo de muestreo 
# Ejemplo: http://156.35.152.161:8001/Tm?Tm=200.0
@app.get("/Tm")
async def create_item(Tm: float):
    freq_event = {"Tm":f"{Tm}"}
    conn = [conn for conn in esp32_websockets]
    await conn[0].send(json.dumps(freq_event))
    return f"Tm enviado: {Tm}"




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
                #print(f"[ESP32] → {time.time()}:{dataBloc}")
               
    except websockets.exceptions.ConnectionClosedError:
        print("ESP32 desconectado")
    finally:
        esp32_websockets.remove(websocket)



# Callback para la creación inicial del servidor WS
async def serve_ws():
    async with websockets.serve(ws_esp32_handler, "0.0.0.0", PORT) as server:
        print("Servidor WebSocket corriendo en puerto 8765")
        await server.serve_forever()  # Nunca termina

# Iniciar WebSocket Server como tarea background
@app.on_event("startup")
async def start_ws_server():
    asyncio.create_task(serve_ws())


