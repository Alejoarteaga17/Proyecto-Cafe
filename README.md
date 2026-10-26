# README

> **Estado arquitectónico:** la arquitectura aprobada es Historical CSV -> API Gateway -> Lambda -> S3 Bronze; sensores simulados -> IoT Core -> Data Firehose -> S3 Bronze; Bronze -> Glue Job 1 -> Silver -> Glue Job 2 -> Gold -> Athena/QuickSight. Los componentes MongoDB, SQS, DLQ, Secrets Manager y SNS fueron eliminados del repositorio por pertenecer a la arquitectura anterior.

- [README](#readme)
  - [Resumen](#resumen)
    - [Pipeline batch: datos históricos del café](#pipeline-batch-datos-históricos-del-café)
    - [Pipeline streaming: sensores de cultivo](#pipeline-streaming-sensores-de-cultivo)
    - [Observabilidad](#observabilidad)
    - [Estructura del repositorio](#estructura-del-repositorio)
  - [Configuración](#configuración)
    - [Contenedor de desarrollo](#contenedor-de-desarrollo)
    - [Variables de entorno](#variables-de-entorno)
    - [Despliegue de la plataforma](#despliegue-de-la-plataforma)
    - [Uso de una plataforma ya desplegada](#uso-de-una-plataforma-ya-desplegada)
  - [Glosario](#glosario)
    - [Variables AWS: `.envs/aws.env`](#variables-aws-envsawsenv)
    - [Variables de Serverless: `.envs/sls.env`](#variables-de-serverless-envsslsenv)

---

## Resumen

`Cultivo de Café Inteligente` es una plataforma de datos para apoyar la toma de decisiones agronómicas en plantaciones de café. Integra datos históricos y telemetría IoT en un data lake S3 con capas Bronze, Silver y Gold.

El proyecto sigue un enfoque de data engineering aplicado: validación, limpieza, particionado, ingestión en streaming, alertas agronómicas y diseño de pipelines serverless sobre AWS, manteniendo el mismo patrón de desacoplamiento y observabilidad para ambos flujos.

### Pipeline batch: datos históricos del café

El flujo batch ingresa datasets históricos (CSV/Kaggle) mediante API Gateway y Lambda. Lambda valida el formato, columnas, filas y tamaño, y conserva el archivo crudo en S3 Bronze. Glue Job 1 limpia, valida, deduplica y particiona de forma estable por `YEAR/MM`; Glue Job 2 agrega a Parquet en Gold. La sobrescritura dinámica de Spark reemplaza solo los períodos recibidos en cada reprocesamiento, sin borrar años históricos no incluidos en la carga.



### Pipeline streaming: sensores de cultivo

Los sensores simulados publican eventos vía MQTT a AWS IoT Core. Una regla los entrega directamente a Amazon Data Firehose, que los almacena en S3 Bronze con prefijos temporales y salida de errores configurada.



### Orquestación, consulta y alcance

Step Functions coordina Glue Job 1 y Glue Job 2 con reintentos y transición de
fallo. Athena consulta las tablas del Glue Data Catalog. QuickSight y la
automatización DataOps se mantienen como trabajo del sprint final; la
documentación no implica que exista un dashboard desplegado.

### Estructura del repositorio

- **`batch/`**: ingestión histórica, Glue Job 1/2, Step Functions, catálogo y
  pruebas del pipeline batch.
- **`streaming/`**: simulador IoT, contrato de sensores, pruebas e
  infraestructura IoT Core → Data Firehose → S3 Bronze.
- **`batch/infrastructure/serverless/data-platform/`**: Glue, Step Functions, Glue Data Catalog y Athena.
- **`frontend/`**: interfaz ligera para pruebas de carga CSV y validación del backend.
- **`docs/`**: diagramas de arquitectura generados con `python3 architecture.py`.
- **`docs/`**: arquitectura, contratos, diccionario, catálogo, lineage, RACI y estado de aceptación.
- **`batch/benchmarks/`**: consultas de Athena para comparar bytes escaneados y tiempo antes/después de las optimizaciones.

La carpeta `streaming/` contiene únicamente la implementación aprobada del
flujo IoT; no se recuperaron componentes legacy de diseños anteriores.

La organización por flujo deja cada pipeline con su propio contexto funcional y su infraestructura asociada, sin depender de carpetas legacy del repositorio.

El detalle de las optimizaciones S3/Athena, las consultas comparables y el
procedimiento para obtener `DataScannedInBytes` y
`TotalExecutionTimeInMillis` está en
[`docs/optimization-benchmark.md`](docs/optimization-benchmark.md). La
implementación está verificada en código/IaC; las métricas de rendimiento
requieren ejecutar las consultas en AWS y permanecen pendientes hasta contar
con ese resultado.

Con esta estructura ya no quedan carpetas duplicadas ni versiones paralelas del mismo proyecto.

Cada subproyecto tiene su propio README con el orden de despliegue y variables de entorno.

### Validación local

Desde el contenedor de desarrollo:

```bash
cd /app
python -m pytest -q batch/tests streaming/tests
```

El resultado local no verifica recursos AWS. Para validar plantillas, ejecutar
`serverless print --stage dev` dentro de cada stack aprobado, incluido
`/app/streaming/infrastructure/serverless/iot`, y revisar el plan antes de
desplegar. No se debe ejecutar un despliegue sin autorización explícita.

El estado detallado y la evidencia se mantienen en
[`docs/acceptance-checklist.md`](docs/acceptance-checklist.md). Los stacks
de los componentes excluidos de la arquitectura anterior fueron eliminados y no
deben reintroducirse.

---

## Configuración

### Contenedor de desarrollo

Estos pasos están pensados para trabajar con Visual Studio Code, pero puedes usar otra IDE siempre que mantengas la misma estructura dockerizada.

1. Instala la extensión `ms-vscode-remote.remote-containers`.
2. Abre la carpeta del proyecto en VS Code. La extensión detectará la configuración del contenedor y te pedirá volver a abrir el proyecto dentro del contenedor.

### Variables de entorno

En la carpeta `.envs` debes crear los archivos con las variables descritas en el glosario.

### Despliegue de la plataforma

Los siguientes comandos están pensados para ejecutarse dentro del contenedor
de desarrollo. Desde una terminal normal, ubicada en la raíz del repositorio,
inicia Docker y entra al contenedor:

```bash
docker compose -f .docker/docker-compose.yml up -d
docker exec -it CoffeeCultivation bash
```

Una vez dentro del contenedor, ejecuta los comandos de despliegue desde
`/app`, con las credenciales AWS configuradas. Para conocer el proceso
completo de configuración o solucionar problemas con Docker, consulta
[`DOCKER_SETUP.md`](DOCKER_SETUP.md).

Los stacks dependen de parámetros SSM y del bucket creado por el stack
`storage`, por lo que deben desplegarse en el siguiente orden:

1. **Crear el almacenamiento S3 Bronze, Silver y Gold**:

   ```bash
   cd /app/batch/infrastructure/serverless/storage
   serverless print --stage dev
   serverless deploy --stage dev
   ```

2. **Publicar los scripts y el código compartido de Glue** en el bucket
   creado en el paso anterior. Sustituye `<data-lake-bucket>` por el nombre
   real del bucket almacenado en el parámetro
   `/<DEPLOY_APP>-storage/DataLakeBucketName` (por defecto,
   `/coffee-cultivation-storage/DataLakeBucketName`):

   ```powershell
   cd /app/batch/glue
   ./publish-scripts.ps1 -BucketName <data-lake-bucket> -Region us-east-1
   ```

   Este paso publica `job_bronze_to_silver.py`,
   `job_silver_to_gold.py` y `coffee-pipeline.zip` bajo el prefijo `glue/`.
   Debe ejecutarse desde un entorno con PowerShell y AWS CLI disponibles. Si
   los scripts ya están publicados en el bucket y no cambiaron, no repitas este
   paso para usar la plataforma.

3. **Crear la plataforma de procesamiento y consulta** (Glue Jobs, Step
   Functions, Glue Data Catalog y Athena):

   ```bash
   cd /app/batch/infrastructure/serverless/data-platform
   serverless print --stage dev
   serverless deploy --stage dev
   ```

4. **Desplegar la API de carga histórica y Lambda**:

   ```bash
   cd /app/batch/serverless
   serverless print --stage dev
   serverless deploy --stage dev
   ```

5. **Desplegar la ingestión IoT** (Thing, política, regla IoT y Data
   Firehose hacia S3 Bronze):

   ```bash
   cd /app/streaming/infrastructure/serverless/iot
   serverless print --stage dev
   serverless deploy --stage dev
   ```

Después del despliegue, configura de forma segura el certificado X.509 del
Thing IoT y ejecuta el simulador según la guía de
[`streaming/README.md`](streaming/README.md). La asociación del certificado
requiere una operación adicional de seguridad de AWS y no queda afirmada por
el stack de Serverless.

#### Validación previa y consideraciones

- Ejecuta `serverless print --stage dev` en **cada** stack antes de ejecutar
  `serverless deploy --stage dev`; revisa nombres, región, bucket, parámetros
  SSM y permisos IAM.
- El orden anterior debe mantenerse: `storage` crea los parámetros que
  consumen los demás stacks y los scripts Glue deben existir en S3 antes de
  crear la plataforma de procesamiento.
- El despliegue crea o actualiza infraestructura en AWS y puede generar
  costos. No ejecutes `serverless deploy` sin autorización explícita.
- La validación local no confirma que los recursos estén desplegados. Ejecuta
  las pruebas desde `/app` con:

  ```bash
  cd /app
  python -m pytest -q batch/tests streaming/tests
  ```

#### Eliminación

Para retirar el entorno, usa `serverless remove --stage dev` en orden inverso:

1. `/app/streaming/infrastructure/serverless/iot`
2. `/app/batch/serverless`
3. `/app/batch/infrastructure/serverless/data-platform`
4. `/app/batch/infrastructure/serverless/storage`

Revisa primero el plan y los recursos dependientes. La eliminación del stack
`storage` borra la infraestructura del data lake y debe realizarse únicamente
cuando ya no se necesiten los datos.

### Uso de una plataforma ya desplegada

Si los stacks ya existen en AWS, **no vuelvas a ejecutar el despliegue para
cada CSV o sesión de sensores**. El despliegue es una operación de
infraestructura; el uso diario consiste en cargar datos, ejecutar el
procesamiento y publicar eventos.

Antes de usar la plataforma, confirma que tienes las credenciales AWS, la
misma región (`us-east-1`) y que estos stacks están en estado `CREATE_COMPLETE`
o `UPDATE_COMPLETE`:

- `<DEPLOY_APP>-storage`
- `<DEPLOY_APP>-data-platform`
- `<DEPLOY_APP>-backend-batch`
- `<DEPLOY_APP>-iot`

Si solo necesitas comprobar la configuración sin modificar recursos, ejecuta
`serverless info --stage dev` desde cada directorio de stack. Si un stack fue
eliminado, está en estado fallido o cambió el nombre de la aplicación,
detente y corrige esa infraestructura antes de enviar datos.

#### Redesplegar cambios del pipeline

No es necesario redesplegar toda la plataforma cada vez que se modifica un
Job de Glue. Primero identifica qué cambió:

- **Solo cambió `batch/glue/job_bronze_to_silver.py`,
  `batch/glue/job_silver_to_gold.py` o código compartido usado por ellos**:
  vuelve a publicar los scripts y el paquete en S3. No redespliegues los
  stacks de storage, API o IoT.
- **Cambió `batch/infrastructure/serverless/data-platform/resources.yml` o
  su `serverless.yml`**: además de publicar los scripts, redespliega
  `data-platform`, porque cambió la definición de Glue, Step Functions,
  Data Catalog o Athena.
- **Cambió `batch/serverless/`**: redespliega el stack `backend-batch`.
- **Cambió `streaming/infrastructure/serverless/iot/`**: redespliega el stack
  `iot`.
- **Cambió `storage`**: no lo redespliegues como una acción rutinaria. Revisa
  primero posibles cambios de bucket, datos y políticas, porque es la base del
  data lake.

##### Caso habitual: cambio solo en un Glue Job

Con los servicios AWS ya desplegados, publica de nuevo los scripts. El
publicador es un script PowerShell (`.ps1`), por lo que normalmente se ejecuta
desde el equipo anfitrión:

```powershell
cd batch/glue
./publish-scripts.ps1 -BucketName <data-lake-bucket> -Region us-east-1
```

Para tu entorno `dev`, el comando exacto es:

```powershell
cd batch/glue
./publish-scripts.ps1 `
  -BucketName coffee-cultivation-coffee-data-lake-dev-aaccode `
  -Region us-east-1
```

La publicación actualiza `glue/job_bronze_to_silver.py`,
`glue/job_silver_to_gold.py` y `glue/coffee-pipeline.zip` en S3. Después,
ejecuta nuevamente `EtlStateMachine` desde Step Functions. La próxima
ejecución usará el código actualizado; no se necesita `serverless deploy`
si no cambió la infraestructura.

##### Caso: cambio en la infraestructura de Glue o Step Functions

Si también cambiaste la definición del stack `data-platform`, valida y
despliega únicamente ese stack después de publicar los scripts:

```bash
cd /app/batch/infrastructure/serverless/data-platform
serverless print --stage dev
serverless deploy --stage dev
```

Luego inicia una nueva ejecución de `EtlStateMachine` y verifica que termine en
`Succeeded`. No ejecutes `serverless remove`: `deploy` actualiza el stack
existente y conserva su nombre y recursos según el plan de CloudFormation.

##### Redespliegue completo

Úsalo cuando haya cambios coordinados en varios componentes o cuando se
requiera actualizar toda la infraestructura. Mantén el orden y valida cada
stack antes de desplegar:

1. Publica los scripts Glue.
2. Despliega `storage` solo si cambió su infraestructura.
3. Despliega `data-platform`.
4. Despliega `backend-batch` si cambió la API o Lambda.
5. Despliega `iot` si cambió la ingestión IoT.

No elimines los stacks para volverlos a crear. Antes de confirmar cada
`serverless deploy`, revisa el cambio propuesto, especialmente cualquier
reemplazo de recursos, cambios de permisos o riesgo para datos existentes.

##### ¿Es obligatorio usar Docker?

No es obligatorio si el equipo anfitrión tiene instaladas y configuradas las
herramientas necesarias: AWS CLI, Node.js, Serverless Framework y PowerShell
para ejecutar `publish-scripts.ps1`, además de las mismas credenciales,
variables (`.envs/aws.env`) y región (`us-east-1`). En ese caso, los comandos
se ejecutan desde las rutas del repositorio del equipo anfitrión, por ejemplo:

```powershell
cd batch/glue
./publish-scripts.ps1 -BucketName <data-lake-bucket> -Region us-east-1
```

Para tu entorno `dev`, reemplaza `<data-lake-bucket>` por
`coffee-cultivation-coffee-data-lake-dev-aaccode`.

Para un despliegue reproducible se recomienda usar Docker, porque el proyecto
instala allí AWS CLI, Serverless, Python y las herramientas de validación. La
imagen actual no instala PowerShell: el script de publicación Glue debe
ejecutarse desde el host o después de instalar `pwsh` en el contenedor. Desde
el host se levanta el contenedor y luego se ejecutan los comandos compatibles
dentro de `/app`, como se explica en
[`DOCKER_SETUP.md`](DOCKER_SETUP.md). El despliegue desde fuera del contenedor
no cambia los recursos por sí mismo; la diferencia es únicamente el entorno
local y las versiones de las herramientas.

#### Levantar nuevamente Docker y el frontend

Si cerraste VS Code, apagaste Docker o detuviste el contenedor, primero
levanta nuevamente el entorno local. Esto **no vuelve a desplegar ni modifica
los servicios de AWS**; únicamente inicia el contenedor de desarrollo para
poder usar la interfaz de carga.

Desde una terminal del equipo anfitrión, ubicada en la raíz del repositorio:

1. Confirma que Docker Desktop está iniciado y que existen
   `.envs/aws.env` y `.envs/sls.env`. Si es la primera configuración, créalos
   según [`DOCKER_SETUP.md`](DOCKER_SETUP.md).
2. Levanta el contenedor:

   ```bash
   docker compose -f .docker/docker-compose.yml up -d
   ```

   Si Docker necesita reconstruir la imagen, usa una sola vez:

   ```bash
   docker compose -f .docker/docker-compose.yml up -d --build
   ```

3. Entra al contenedor:

   ```bash
   docker exec -it CoffeeCultivation bash
   ```

   También puedes abrir el proyecto nuevamente en VS Code y seleccionar
   **Reopen in Container**.
4. Dentro del contenedor, sirve el frontend:

   ```bash
   cd /app
   python3 -m http.server 8080 --directory frontend
   ```

5. Mantén esa terminal abierta. En VS Code abre la pestaña **Ports**, agrega
   el puerto `8080` si no aparece y abre la dirección reenviada. Como
   alternativa, si VS Code ya reenvía el puerto, abre
   `http://localhost:8080` en el navegador del equipo anfitrión.

El servidor HTTP se detiene con `Ctrl+C`; detenerlo no elimina los archivos ni
los recursos AWS. Para volver a cargar otro CSV después, basta con iniciar de
nuevo el servidor del frontend y repetir el procedimiento de carga. No es
necesario usar Postman.

#### Enviar un nuevo CSV histórico

1. Obtén la URL y la API Key del stack de carga histórica. La URL puede
   consultarse con:

   ```bash
   cd /app/batch/serverless
   serverless info --stage dev
   ```

   La API Key creada por el stack puede consultarse desde API Gateway o, si
   tienes permiso para leer su valor, con:

   ```bash
   aws apigateway get-api-keys \
     --include-values \
     --query "items[?name=='<DEPLOY_APP>-backend-batch-key'].value | [0]" \
     --output text \
     --region us-east-1
   ```

   Sustituye `<DEPLOY_APP>` por el valor utilizado al desplegar; si no se
   definió, es `coffee-cultivation`. No guardes la API Key en el repositorio ni
   la incluyas en capturas o scripts compartidos.

2. Si todavía no levantaste el frontend, hazlo desde el contenedor:

   ```bash
   cd /app
   python3 -m http.server 8080 --directory frontend
   ```

   Abre `http://localhost:8080` o la URL del puerto reenviado en VS Code,
   introduce la URL de API Gateway y la API Key, selecciona el archivo y pulsa
   **Publicar CSV**. El CSV debe ser UTF-8, contener exactamente las 19
   columnas requeridas, tener entre 1 y 300 filas y no superar 5 MiB. El
   frontend rechaza localmente archivos mayores antes de codificarlos en
   Base64. Una
   respuesta HTTP `202` confirma que Lambda lo aceptó y lo guardó en
   `bronze/historical/`; no confirma que ya haya llegado a Silver o Gold.
   Archivos mayores requieren un flujo de carga por partes o directo a S3
   validado antes de Bronze; ese flujo no está implementado en este endpoint.

3. Ejecuta la máquina `EtlStateMachine` desde Step Functions. La carga del CSV
   no la inicia automáticamente. En la consola de AWS:

   - Abre **Step Functions** en `us-east-1`.
   - Selecciona la máquina del stack `data-platform`.
   - Elige **Start execution** y usa `{}` como entrada.
   - Espera el estado `Succeeded` antes de consultar Gold en Athena.

   La ejecución realiza Glue Job 1 (Bronze -> Silver) y, solo si termina
   correctamente, Glue Job 2 (Silver -> Gold). Si necesitas automatizar este
   inicio para cada carga, esa integración no está implementada actualmente y
   debe tratarse como una ampliación separada.

#### Activar el flujo de sensores IoT

El stack IoT permanece desplegado y Firehose puede recibir eventos sin volver a
desplegarlo. Para enviar eventos se necesita además un certificado X.509
activo, asociado al Thing creado por el stack y con la política IoT adjunta.
Esa asociación no la realiza el template de Serverless.

El simulador incluido actualmente **genera y valida eventos, pero solo los
imprime en la salida estándar**; no es todavía un cliente MQTT. Por tanto,
ejecutarlo así no activa el streaming en AWS:

```bash
cd /app/streaming
python3 simulator/simulate_coffee_sensors.py --count 3 --seed 7 --interval 0
```

Para publicar eventos reales, usa un cliente MQTT compatible con AWS IoT Core,
configurado con el endpoint IoT de la cuenta, el certificado del Thing, la
clave privada y el certificado raíz de Amazon Trust Services. Publica cada
payload en:

```text
sensors/coffee/<ThingName>/data
```

El `<ThingName>` debe ser el Thing asociado al certificado. El stack añade
`sensor_id` a partir del tercer segmento del topic y después entrega el
evento a Firehose. Verifica el nombre del Thing con el parámetro SSM creado
por el stack o desde la consola de IoT Core:

```bash
aws ssm get-parameter \
  --name "/<DEPLOY_APP>-iot/SensorThingName" \
  --query "Parameter.Value" \
  --output text \
  --region us-east-1
```

Después de publicar, espera el intervalo de buffering configurado de Firehose
(hasta 60 segundos o 5 MiB) y verifica que aparezca un objeto GZIP en
`bronze/iot/year=YYYY/month=MM/day=DD/`. Un evento en la carpeta
`bronze/iot-errors/` indica un fallo de entrega y debe investigarse; no debe
tratarse como una entrega exitosa.

La creación y asociación del certificado son operaciones de seguridad de AWS
que no están automatizadas en el repositorio. Si todavía no existe esa
configuración, primero debe completarse en IoT Core; no basta con ejecutar el
simulador local.

---

## Glosario

### Variables AWS: `.envs/aws.env`

- `AWS_ACCESS_KEY_ID`: clave de acceso para desplegar stacks en AWS.
- `AWS_SECRET_ACCESS_KEY`: clave secreta asociada a la anterior.
- `AWS_DEFAULT_REGION`: región objetivo del despliegue.
- `AWS_DEFAULT_OUTPUT`: formato de salida por defecto del CLI de AWS.

### Variables de Serverless: `.envs/sls.env`

- `SERVERLESS_ACCESS_KEY`: clave de acceso de Serverless Framework necesaria para despliegues y validaciones del CLI.
