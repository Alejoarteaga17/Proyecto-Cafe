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

La página solo sirve para pruebas rápidas y no reemplaza ni modifica la
arquitectura del backend ni la infraestructura AWS del proyecto.

## Alcance

La interfaz solo prueba la carga histórica hacia API Gateway. El consumo analítico mediante Athena y QuickSight está reservado para el sprint final; no se conecta a MongoDB ni expone credenciales.
