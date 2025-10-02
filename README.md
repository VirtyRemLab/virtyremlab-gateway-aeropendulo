# Descripción

Gateway WS<->WS par conectar el ESP32 que gobierna el aeropéndulo al backend del sistema VirtyRemLab. El servicio es una API de FastAPI que además integra un servidor websockets para la comunicación en tiempo real con el ESP32. La API ofrece varios endpoints para comprobar el estado de la conexión. 

El servidor web empleado para alojar la API es uvinicorn. 

# Desarrollo
Ejecución del servicio en local (desarrollo):
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1 --loop uvloop
```

# Despliegue
Para el despliegue se empleará un contenedor de docker. 

