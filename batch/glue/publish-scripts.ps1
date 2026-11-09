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
$staging = Join-Path $env:TEMP "coffee-glue-package"

if (Test-Path $staging) {
    Remove-Item -Path $staging -Recurse -Force
}
New-Item -Path $staging -ItemType Directory | Out-Null

Copy-Item (Join-Path $scriptRoot "job_bronze_to_silver.py") $staging
Copy-Item (Join-Path $scriptRoot "job_silver_to_gold.py") $staging

$packageRoot = Join-Path $staging "src"
New-Item -Path $packageRoot -ItemType Directory | Out-Null
Copy-Item (Join-Path $projectRoot "src/common") $packageRoot -Recurse
Copy-Item (Join-Path $projectRoot "src/pipeline") $packageRoot -Recurse

$zipPath = Join-Path $staging "coffee-pipeline.zip"
Compress-Archive -Path $packageRoot -DestinationPath $zipPath

aws s3 cp (Join-Path $staging "job_bronze_to_silver.py") "s3://$BucketName/$Prefix/job_bronze_to_silver.py" --region $Region
aws s3 cp (Join-Path $staging "job_silver_to_gold.py") "s3://$BucketName/$Prefix/job_silver_to_gold.py" --region $Region
aws s3 cp $zipPath "s3://$BucketName/$Prefix/coffee-pipeline.zip" --region $Region

Write-Host "Published Glue scripts to s3://$BucketName/$Prefix/"