# Calidad y gobernanza de datos

Esta carpeta contiene la documentación operativa y técnica para gobernar los
datos del proyecto de cultivo inteligente de café.

## Contenido

- [Diccionario de datos](./data-dictionary.md): campos, tipos, unidades y
  significado de los datasets batch y streaming.
- [Catálogo de datos](./data-catalog.md): inventario de activos, propietarios,
  ubicación lógica y ciclo de vida por capa.
- [Reglas de calidad](./quality-rules.md): reglas implementadas en los
  validadores Lambda y reglas previstas para Glue.
- [Gobernanza](./governance.md): responsabilidades, clasificación, acceso,
  retención y trazabilidad.
- [Calidad de código](./code-quality.md): controles para cambios Python,
  IaC, pruebas y documentación.

## Estado de implementación

La documentación diferencia explícitamente entre controles implementados y
controles planificados:

- **Implementado:** validación de columnas, tipos básicos, rangos, tamaño
  máximo del batch, validación de payloads de sensores, alertas agronómicas y
  carga segura a Bronze mediante URL prefirmada.
- **En preparación:** ejecución administrada de Glue, catálogo de Glue,
  orquestación con Step Functions, reglas EventBridge y consultas Athena.

Las reglas de este directorio deben actualizarse junto con el código que las
implementa. Cada cambio de esquema debe actualizar también el diccionario y
el catálogo.
