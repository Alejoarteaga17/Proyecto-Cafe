#!/usr/bin/env bash
set -euo pipefail

workflow="${1:-historical}"
stage="${2:-dev}"
input_prefix="${3:-}"
region="${AWS_REGION:-us-east-1}"

case "$workflow" in
  historical)
    export_name="data-platform-${stage}-HistoricalStateMachineArn"
    default_input="bronze/historical/"
    ;;
  iot)
    export_name="data-platform-${stage}-IotStateMachineArn"
    default_input="bronze/iot/"
    ;;
  *)
    printf 'Unsupported workflow: %s. Use historical or iot.\n' "$workflow" >&2
    exit 2
    ;;
esac

input_prefix="${input_prefix:-$default_input}"
bucket="${DATA_LAKE_BUCKET:-}"
if [[ -z "$bucket" ]]; then
  app="${DEPLOY_APP:-coffee-cultivation}"
  bucket="$(aws ssm get-parameter \
    --name "/${app}-storage/DataLakeBucketName" \
    --region "$region" \
    --query 'Parameter.Value' \
    --output text)"
fi
output_prefix="${OUTPUT_PREFIX:-}"
state_machine_arn="$(aws cloudformation list-exports \
  --region "$region" \
  --query "Exports[?Name=='${export_name}'].Value | [0]" \
  --output text)"

if [[ -z "$state_machine_arn" || "$state_machine_arn" == "None" ]]; then
  printf 'Could not find CloudFormation export %s.\n' "$export_name" >&2
  exit 1
fi

if [[ -z "$output_prefix" ]]; then
  if [[ "$workflow" == "historical" ]]; then
    output_prefix="silver/historical/"
  else
    output_prefix="silver/iot/"
  fi
fi
gold_prefix="${GOLD_PREFIX:-}"
if [[ -z "$gold_prefix" ]]; then
  if [[ "$workflow" == "historical" ]]; then
    gold_prefix="gold/historical/"
  else
    gold_prefix="gold/iot/"
  fi
fi

execution_input="$(python3 - "$bucket" "$input_prefix" "$output_prefix" "$gold_prefix" <<'PY'
import json
import sys

print(json.dumps({
    "bucket": sys.argv[1],
    "input_prefix": sys.argv[2],
    "output_prefix": sys.argv[3],
    "gold_prefix": sys.argv[4],
}))
PY
)"

aws stepfunctions start-execution \
  --state-machine-arn "$state_machine_arn" \
  --input "$execution_input" \
  --region "$region"
