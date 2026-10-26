# Gobernanza de datos

## Responsabilidades

| Rol | Responsabilidad |
|---|---|
| Propietario funcional | Define el significado y uso de los datos agronómicos |
| Responsable técnico | Mantiene IaC, pipelines, esquemas y permisos |
| Responsable de calidad | Revisa reglas, métricas y registros en quarantine |
| Consumidor analítico | Consulta Gold mediante Athena y reporta anomalías |

## Principios

- Bronze es inmutable desde la perspectiva del procesamiento: conserva la
  fuente original.
- Silver contiene datos tipados, validados y particionados.
- Gold contiene agregados analíticos, no reemplaza la fuente.
- Todo rechazo debe conservar el motivo y el identificador de carga.
- Los cambios de esquema requieren actualizar código, diccionario y catálogo.
- Los secretos se gestionan con servicios de AWS y nunca en Git.
- El acceso debe seguir mínimo privilegio y separarse por ambiente.

## Trazabilidad mínima

Cada carga debe poder relacionarse con:

- `dataset_id`.
- Clave S3 de Bronze.
- Fecha de ingestión.
- Ruta Silver/Gold generada.
- Cantidad de filas leídas, válidas y rechazadas.
- Versión del código o despliegue que la procesó.

La trazabilidad completa quedará operativa cuando Step Functions y Glue
persistan los metadatos de ejecución en una ruta de auditoría.
