# Frontend de carga y dashboard QuickSight

Esta carpeta contiene una aplicación web única con dos pestañas: una para
arrastrar un CSV local hacia el endpoint de validación batch y otra para
embeber el dashboard publicado de QuickSight mediante una URL temporal
generada por Lambda. Ambas se sirven desde el mismo origen HTTP y comparten la
API Key en memoria.

## Requisitos

- La API de carga histórica debe estar desplegada y disponible en API Gateway.
- Debes tener la URL completa del endpoint `/coffee-historical-data`.
- Debes tener una API Key válida de API Gateway. La página no genera ni
  almacena la clave.
- El navegador debe poder acceder al servidor local y la API debe aceptar
  solicitudes CORS.

La interfaz trae una URL de API como valor inicial para facilitar las pruebas,
pero debes verificarla con `serverless info --stage dev` y reemplazarla si
corresponde a otro stage, cuenta o despliegue. La API Key siempre debe
introducirse manualmente.

## Cómo usarla

### Opción recomendada: dentro del contenedor Docker

Si estás trabajando dentro del contenedor `CoffeeCultivation`, desde `/app`
ejecuta:

```bash
python3 -m http.server 8080 --bind 0.0.0.0 --directory frontend
```

Como el Compose del proyecto no publica el puerto `8080` directamente,
reenvíalo desde la pestaña **Ports** de VS Code y abre la URL que VS Code
asigne. Si el puerto ya fue reenviado, también puedes abrir:

```text
http://localhost:8080
```

### Opción alternativa: desde la terminal del equipo

Si el equipo tiene Python 3 instalado, no es necesario entrar al contenedor:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory frontend
```

En este caso, abre directamente `http://localhost:8080`.

### Publicar el archivo

1. Arrastra el CSV a la zona de carga o haz clic para seleccionarlo.
2. Introduce la URL completa de API Gateway, incluyendo
   `/coffee-historical-data`.
3. Pega la API Key temporalmente en el campo correspondiente.
4. Pulsa **Publicar CSV**.

Una respuesta HTTP `202` significa que Lambda validó y guardó el CSV en S3
Bronze y creó una ejecución de `HistoricalEtlStateMachine`. El procesamiento
continúa de forma asíncrona hacia Silver y Gold; el campo
`etl_execution_arn` identifica la ejecución para consultar su estado en
Step Functions.

## Abrir el dashboard

1. Despliega el endpoint `coffee-dashboard/embed-url` del stack batch.
2. Ejecuta el servidor local:

   ```bash
   python3 -m http.server 8080 --bind 0.0.0.0 --directory frontend
   ```

3. Abre `http://localhost:8080/`.
4. Introduce la API Key en el campo compartido de la parte superior. Luego,
   en la pestaña **Dashboard**, pulsa **Cargar dashboard**.

La pestaña **Publicar CSV** queda disponible en la misma página. El enlace
antiguo `dashboard.html` redirige a `index.html#dashboard` para conservar
compatibilidad con marcadores existentes.

### Generar simulación IoT desde el frontend

En la pestaña **Simulación IoT**, introduce la cantidad de eventos (`count`),
el intervalo en segundos (`interval`) y, opcionalmente, una semilla. Pulsa
**Iniciar simulación**. La API inicia el simulador en segundo plano; cada
evento se publica en IoT Core y activa automáticamente el flujo Firehose,
Bronze y `IotEtlStateMachine`. Se permiten de 1 a 100 eventos y un intervalo
de 0 a 60 segundos.

La página no contiene credenciales AWS ni consulta S3/Athena directamente. El
endpoint Lambda genera una URL de sesión temporal para el usuario registrado
de QuickSight y la API Key se usa solo en memoria.

Si la página muestra un error HTTP, revisa que uses la API Key activa del stack
`backend-batch` y que la URL termine exactamente en
`/coffee-dashboard/embed-url`. La página agrega un parámetro anti-cache para
evitar respuestas antiguas de API Gateway.

El despliegue permite `http://localhost:8080` por defecto. QuickSight no
acepta `http://127.0.0.1:8080` como dominio HTTP de embedding; abre la página
usando `localhost`.

## Nota importante

El frontend lee el archivo local como bytes, lo convierte a Base64 y envía un
`POST` con el campo `file`, que es el formato esperado por Lambda.
El endpoint actual acepta archivos de hasta 5 MiB y la validación del backend
también limita el dataset a 300 filas. El frontend rechaza archivos mayores
antes de convertirlos a Base64 para evitar una solicitud que exceda los límites
de transporte de API Gateway/Lambda y termine mostrando un error genérico del
navegador.

Para archivos mayores, no basta con aumentar la constante del backend: habría
que implementar un flujo de carga por partes o una carga directa controlada a
S3 y mantener la validación antes de promover el archivo a Bronze. Ese cambio
no forma parte del endpoint actual.

La página solo sirve para pruebas rápidas y no reemplaza ni modifica la
arquitectura del backend ni la infraestructura AWS del proyecto.

## Alcance

La carga histórica y el dashboard son pestañas independientes dentro de la
misma aplicación. El consumo usa QuickSight y no introduce MongoDB, SQS ni una
base operativa.
