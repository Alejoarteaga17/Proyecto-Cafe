# Frontend de prueba para publicar un CSV

Esta carpeta contiene una interfaz mínima para arrastrar un CSV local hacia el
endpoint de validación batch.

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
Bronze. No significa que los datos ya estén en Silver o Gold; después debes
iniciar `HistoricalEtlStateMachine` desde Step Functions.

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
