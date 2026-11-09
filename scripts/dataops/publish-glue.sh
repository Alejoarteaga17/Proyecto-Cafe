#!/usr/bin/env bash
set -euo pipefail

stage="${1:-dev}"
region="${AWS_REGION:-us-east-1}"
app="${DEPLOY_APP:-coffee-cultivation}"
prefix="${GLUE_SCRIPT_PREFIX:-glue}"
storage_stack="${app}-storage"
if [[ "$stage" != "dev" ]]; then
  storage_stack="${storage_stack}-${stage}"
fi

bucket="$(aws ssm get-parameter \
  --name "/${storage_stack}/DataLakeBucketName" \
  --region "$region" \
  --query 'Parameter.Value' \
  --output text)"

workspace="$(mktemp -d)"
trap 'rm -rf "$workspace"' EXIT

mkdir -p "$workspace/batch/src" "$workspace/iot/streaming_src"
cp batch/glue/job_bronze_to_silver.py batch/glue/job_silver_to_gold.py "$workspace/batch/"
cp -R batch/src/common batch/src/pipeline "$workspace/batch/src/"
cp streaming/glue/job_iot_bronze_to_silver.py streaming/glue/job_iot_silver_to_gold.py "$workspace/iot/"
cp -R streaming/streaming_src "$workspace/iot/"

(cd "$workspace/batch" && zip -qr "$workspace/coffee-pipeline.zip" src)
(cd "$workspace/iot" && zip -qr "$workspace/coffee-iot-pipeline.zip" streaming_src)

aws s3 cp "$workspace/batch/job_bronze_to_silver.py" \
  "s3://${bucket}/${prefix}/job_bronze_to_silver.py" --region "$region"
aws s3 cp "$workspace/batch/job_silver_to_gold.py" \
  "s3://${bucket}/${prefix}/job_silver_to_gold.py" --region "$region"
aws s3 cp "$workspace/coffee-pipeline.zip" \
  "s3://${bucket}/${prefix}/coffee-pipeline.zip" --region "$region"
aws s3 cp "$workspace/iot/job_iot_bronze_to_silver.py" \
  "s3://${bucket}/${prefix}/job_iot_bronze_to_silver.py" --region "$region"
aws s3 cp "$workspace/iot/job_iot_silver_to_gold.py" \
  "s3://${bucket}/${prefix}/job_iot_silver_to_gold.py" --region "$region"
aws s3 cp "$workspace/coffee-iot-pipeline.zip" \
  "s3://${bucket}/${prefix}/coffee-iot-pipeline.zip" --region "$region"

printf 'Glue scripts published to s3://%s/%s/ for stage %s\n' "$bucket" "$prefix" "$stage"
