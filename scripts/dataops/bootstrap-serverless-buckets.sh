#!/usr/bin/env bash
set -euo pipefail

stage="${1:?Usage: bootstrap-serverless-buckets.sh <stage>}"
region="${AWS_REGION:-us-east-1}"
app="${DEPLOY_APP:-coffee-cultivation}"
developer="${DEVELOPER:-aaccode}"

case "$stage" in
  dev)
    suffix="-${developer}"
    ;;
  test|prod)
    suffix=""
    ;;
  *)
    echo "Unsupported stage: $stage" >&2
    exit 1
    ;;
esac

create_or_configure_bucket() {
  local bucket="$1"

  if ! aws s3api head-bucket --bucket "$bucket" --region "$region" >/dev/null 2>&1; then
    aws s3api create-bucket --bucket "$bucket" --region "$region"
  fi

  aws s3api put-bucket-versioning \
    --bucket "$bucket" \
    --versioning-configuration Status=Enabled
  aws s3api put-public-access-block \
    --bucket "$bucket" \
    --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-encryption \
    --bucket "$bucket" \
    --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
}

for service in storage data-platform backend-batch iot; do
  create_or_configure_bucket \
    "${region}-cfn-${service}-${stage}${suffix}-deploys"
done
