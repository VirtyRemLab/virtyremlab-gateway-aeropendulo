
######################################################################
# Gateway WS<->WS par conectar el ESP32 que gobierna el aeropéndulo al 
# backend del sistema VirtyRemLab-
# El servicio lo
# Autor: Diego García
######################################################################

import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import websockets
import struct
import json
from pydantic import BaseModel
import time
import nats 



PORT = 8765
NATS_SERVERS = []


# Callback para la creación inicial del servidor WS
async def serve_ws():
    async with websockets.serve(ws_esp32_handler, "0.0.0.0", PORT) as server:
        print("Servidor WebSocket corriendo en puerto 8765")
        await server.serve_forever()  # Nunca termina
    

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Servidor ws para la conexión con el ESP32
    asyncio.create_task(serve_ws())
    # Nos conectamos al broker NATS
    NATS_SERVERS.append(await nats.connect("nats://demo.nats.io:4222"))
    yield 
    # Cuando acaba la aplicación el yield reanuda la ejecución aquí
    # Se desconecta del NATS
    await NATS_SERVERS[0].drain()


# Crear aplicación FastAPI
app = FastAPI(lifespan=lifespan)
# app = FastAPI()


# Request body
class DeviceStatus(BaseModel):
    device_id: str
    connected: bool

STATUS = DeviceStatus(device_id="esp-aeropendulo",connected = False)
# Método post para cambiar el periodo de muestreo 
# Ejemplo: http://156.35.152.161:8001/Tm?Tm=200.0
@app.get("/Tm")
async def create_item(Tm: float):
    freq_event = {"Tm":f"{Tm}"}
    conn = [conn for conn in esp32_websockets]
    await conn[0].send(json.dumps(freq_event))
    return f"Tm enviado: {Tm}"



@app.get("/status", response_model=DeviceStatus)
async def device_status():
    return STATUS


    # pong_waiter = await conn[0].ping()
    # try:
    #     latency = await pong_waiter
    #     return DeviceStatus(device_id="esp-aeropendulo",
    #                         connected=True)
    # except ConnectionClosed or ConcurrencyError:
    #     return DeviceStatus(device_id="esp-aeropendulo",
    #                         connected=False)





#####################################################################################
## Gestión de la conexión con el ESP32
#####################################################################################

# Guardar el estado del ESP32 (si necesitas enviarle datos)
esp32_websockets = set()

# Handler de mensajes WebSocket
async def ws_esp32_handler(websocket):
    print("ESP32 conectado")
    STATUS.connected = True
    esp32_websockets.add(websocket)
    try:
        async for message in websocket:
            if isinstance(message,bytes):
                dataBloc = struct.unpack("<ff",message)
                print(f"[ESP32] → {time.time()}:{dataBloc}")
                # TODO. deshacer el stream de bytes en variables del proceso y enviarlas una a una.
                #      Sería más eficiente retransmitir el stream al completo, pero menos interpretable y estructurado.
                await NATS_SERVERS[0].publish("aeropendulo.esp32.y", message)
               
    except websockets.exceptions.ConnectionClosedError:
        print("ESP32 desconectado")
        STATUS.connected = False
    finally:
        esp32_websockets.remove(websocket)





# # Iniciar WebSocket Server como tarea background
# @app.on_event("startup")
# async def start_ws_server():
  


