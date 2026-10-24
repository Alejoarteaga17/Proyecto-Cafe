# Frontend de prueba para carga de CSV

Esta carpeta contiene una mini interfaz para enviar un archivo CSV al endpoint de validación batch del backend.

## Cómo usarla

1. Abre el archivo `frontend/index.html` directamente en el navegador o sirve la carpeta con un pequeño servidor local.
2. Reemplaza estas dos constantes con tus valores reales:

```js
const API_URL = 'https://<api-id>.execute-api.us-east-1.amazonaws.com/dev/coffee-historical-data';
const API_KEY = 'COLOCA_AQUI_LA_API_KEY_GENERADA_POR_EL_BACKEND';
```

3. Selecciona un CSV y pulsa **Enviar al backend**.

## Nota importante

La lógica del frontend convierte el CSV a base64 antes del `POST`, igual que el backend espera recibir el campo `file`.

La página solo sirve para pruebas rápidas y no reemplaza ni modifica la arquitectura del backend ni la infraestructura AWS del proyecto.

## Alcance

La interfaz solo prueba la carga histórica hacia API Gateway. El consumo analítico mediante Athena y QuickSight está reservado para el sprint final; no se conecta a MongoDB ni expone credenciales.
