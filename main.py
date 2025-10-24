
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
MSG_LENGH_FLOATS = 10
NATS_SERVERS = []


#TODO: Sacar la configuración de la comunicación a un archivo externo que lo compartan
# todas las imágenes de docker
AEROPENDULO_COMS_CONFIG = {
    "lenght":11,
    "model":{ "mode": "estado del sistema [STANDBY, READY,TEST, PID, ALARM]",
             "yk": "salida del sistema",
             "rk": "Referencia",
             "uk": "Acción de control",
             "ek": "Error del sistema",
             "M1": "Vel del motor 1",
             "M2": "Vel del motor 2",
             "vel_man": "Consigna para la velocidad manual",
             "Kp": "Consigna para la ganancia proporcional del regulador PID",
             "Ki": "Consigna para la ganancia integral del regulador PID",
             "Kd": "Consigna para la ganancia diferencial del regulador PID"
    },
    "interface":{"event": "mandar eventos al ESP enum EVENTS {NONE:0,POWERON:1,POWEROFF:2,START_PID:3,START_TEST:4,STOP:4,RESET:5,FAULT:6"},
                 "vel_man": "Cambiar la vel manual",
                 "Kp":"Cambiar la Kp del sistema",
                 "Ki":"Cambiar la Ki del sistema",
                 "Kd":"Cambiar la Kd del sistema"

}

# Guardar el estado del ESP32 (si necesitas enviarle datos)
esp32_websockets = set()

# Callback para la creación inicial del servidor WS
async def serve_ws():
    server = await websockets.serve(ws_esp32_handler, "0.0.0.0", PORT) 
    print("Servidor WebSocket corriendo en puerto 8765")
    await server.serve_forever()  # Nunca termina
    esp32_websockets.add(server)

async def cb_freq(msg):
    subject = msg.subject
    reply = msg.reply
    data =  struct.unpack("f",msg.data)[0]
    print("Received a message on '{subject} {reply}': {data}".format(
        subject=subject, reply=reply, data=data))
    
    val = data if not isinstance(data,(int,float)) else str(data)
    
    freq_event = {"freq":val}
    conn = [conn for conn in esp32_websockets]
    await conn[0].send(json.dumps(freq_event))    

async def cb_generic(msg):

    subject = msg.subject
    command = subject.split(".")[-1]
    reply = msg.reply
    data =  struct.unpack("f",msg.data)[0]
    print(f"{subject}")
    print("Received a message on '{command}': {data}".format(
        command=command, data=data))
    
    val = data if not isinstance(data,(int,float)) else str(data)
    
    event = {command:val}
    conn = [conn for conn in esp32_websockets]
    await conn[0].send(json.dumps(event))    

# async def cb_generic2(msg):

#     subject = msg.subject
#     command = subject.split(".")[-1]
#     reply = msg.reply
#     data =  struct.unpack("f",msg.data)[0]
#     print(f"{subject}")
#     print("Received a message on '{command}': {data}".format(
#         command=command, data=data))
    
#     val = data if not isinstance(data,(int,float)) else str(data)
    
#     event = {command:val}
#     conn = [conn for conn in esp32_websockets]
#     await conn[0].send(json.dumps(event))    


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Servidor ws para la conexión con el ESP32
    asyncio.create_task(serve_ws())
    # Nos conectamos al broker NATS
    NATS_SERVERS.append(await nats.connect("nats://localhost:4222"))
    subs = []

    for k,v in AEROPENDULO_COMS_CONFIG["interface"].items():
        subs.append(await NATS_SERVERS[0].subscribe(f"aeropendulo.esp32.{k}", cb=cb_generic))
    
    yield 
    # Cuando acaba la aplicación el yield reanuda la ejecución aquí
    # Se desconecta del NATS
    for sub in subs:
        await sub.unsubscribe()
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




#####################################################################################
## Gestión de la conexión con el ESP32
#####################################################################################



# Handler de mensajes WebSocket
async def ws_esp32_handler(websocket):
    print("ESP32 conectado")
    STATUS.connected = True
    esp32_websockets.add(websocket)
    try:
        async for message in websocket:
            if isinstance(message,bytes):
                dataBloc = struct.unpack("<"+"f"*AEROPENDULO_COMS_CONFIG["lenght"],message)
                print(f"[ESP32] → {time.time()}:{dataBloc}")
                await NATS_SERVERS[0].publish(f"aeropendulo.esp32.state", message)
                # for i,(k,v) in enumerate(AEROPENDULO_COMS_CONFIG["model"].items()):
                #     await NATS_SERVERS[0].publish(f"aeropendulo.esp32.{k}", struct.pack("f",dataBloc[i]))
                    #print(f"{i}:{k}:{v}{dataBloc[i]}")
               
    except websockets.exceptions.ConnectionClosedError:
        print("ESP32 desconectado")
        STATUS.connected = False
    finally:
        esp32_websockets.remove(websocket)





# # Iniciar WebSocket Server como tarea background
# @app.on_event("startup")
# async def start_ws_server():
  


