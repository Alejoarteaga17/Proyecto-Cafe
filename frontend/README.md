# Frontend de prueba para publicar un CSV

Esta carpeta contiene una interfaz mínima para arrastrar un CSV local hacia el
endpoint de validación batch.

## Cómo usarla

1. Sirve la carpeta con un servidor local:

```bash
python3 -m http.server 8080 --directory frontend
```

2. Abre `http://localhost:8080`.
3. Arrastra el CSV a la zona de carga o haz clic para seleccionarlo.
4. Confirma la URL de API Gateway.
5. Pega la API Key temporalmente en el campo correspondiente.
6. Pulsa **Publicar CSV**.

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

La interfaz solo prueba la carga histórica hacia API Gateway. El consumo analítico mediante Athena y QuickSight está reservado para el sprint final; no se conecta a MongoDB ni expone credenciales.
