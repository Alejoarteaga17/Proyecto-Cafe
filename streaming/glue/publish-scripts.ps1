[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BucketName,

    [string]$Prefix = "glue",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$staging = Join-Path $env:TEMP "coffee-iot-glue-package"

if (Test-Path $staging) {
    Remove-Item -Path $staging -Recurse -Force
}
New-Item -Path $staging -ItemType Directory | Out-Null

Copy-Item (Join-Path $scriptRoot "job_iot_bronze_to_silver.py") $staging
Copy-Item (Join-Path $scriptRoot "job_iot_silver_to_gold.py") $staging

$packageRoot = Join-Path $staging "streaming_src"
Copy-Item (Join-Path $projectRoot "streaming_src") $packageRoot -Recurse

$zipPath = Join-Path $staging "coffee-iot-pipeline.zip"
Compress-Archive -Path $packageRoot -DestinationPath $zipPath

aws s3 cp (Join-Path $staging "job_iot_bronze_to_silver.py") `
  "s3://$BucketName/$Prefix/job_iot_bronze_to_silver.py" --region $Region
aws s3 cp (Join-Path $staging "job_iot_silver_to_gold.py") `
  "s3://$BucketName/$Prefix/job_iot_silver_to_gold.py" --region $Region
aws s3 cp $zipPath "s3://$BucketName/$Prefix/coffee-iot-pipeline.zip" `
  --region $Region

Write-Host "Published IoT Glue scripts to s3://$BucketName/$Prefix/"
