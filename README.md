# Descripción

Gateway WS<->WS par conectar el ESP32 que gobierna el aeropéndulo al backend del sistema VirtyRemLab. El servicio es una API de FastAPI que además integra un servidor websockets para la comunicación en tiempo real con el ESP32. La API ofrece varios endpoints para comprobar el estado de la conexión. 

El servidor web empleado para alojar la API es uvinicorn. 

# Desarrollo
Ejecución del servicio en local (desarrollo):
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1 --loop uvloop
```

# Despliegue
Para el despliegue se empleará un contenedor de docker. La imagen se crear a partir del ```Dockerfile```.

Creación de la imagen:

```bash
docker build -t gateway-esp-aeropendulo:v0.1 .
```

Ejecutar el contenedor para la imagen creada:
```bash 
docker run -d -p 8001:8000 -p 8765:8765 --name gateway-esp-aeropendulo gateway-esp-aeropendulo:v0.1
```

# NATS
Los mensajes recibidos por websockets del ESP se reenviarán a un servidor NATS. Este servidor es otro contenedor de docker que se ejecutará como:
```bash
docker pull nats:latest
docker run -p 4222:4222 -ti nats:latest
```

# Modelos de los datos [en pruebas] 

El gateway recibe un array de dos valores binarios. El primero de ellos simula el seno y el segundo siempre es 0. Se definen los siguientes tópicos para el servidor NATS:

- aeropendulo.esp32.y
- aeropendulo.esp32.nulo

