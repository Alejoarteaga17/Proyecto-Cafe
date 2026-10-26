# Calidad de código e infraestructura

## Controles antes de un pull request

```powershell
python -m compileall -q batch/src batch/glue
python -m pytest batch/tests
git diff --check
npx.cmd serverless package --stage dev
```

El empaquetado debe ejecutarse por cada stack modificado y no debe reemplazar
`deploy` durante la revisión.

## Criterios de aceptación

- La sintaxis Python compila.
- Las pruebas unitarias pasan.
- No se introducen secretos ni archivos generados.
- Las políticas IAM son específicas y no usan comodines innecesarios.
- Los nombres y regiones respetan el ambiente objetivo.
- La documentación refleja los recursos realmente provisionados.
- La plantilla CloudFormation contiene los recursos que el README declara.

## Evidencia de despliegue

Conservar en el reporte de entrega:

1. Estado `CREATE_COMPLETE` o `UPDATE_COMPLETE` de cada stack.
2. Nombre y región de los recursos.
3. Logs de Lambda y Glue.
4. Ejecución exitosa de Step Functions.
5. Objetos Bronze, Silver y Gold.
6. Consulta Athena con resultados.

No guardar tokens, claves, URLs prefirmadas ni API keys en capturas o
documentación versionada.
