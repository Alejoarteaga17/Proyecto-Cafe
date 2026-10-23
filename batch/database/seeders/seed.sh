#!/bin/bash
# Seeds coffee historical data and coffee sensor readings with realistic synthetic data.
# Refuses to run unless the MongoCredentials secret is tagged STAGE=dev or
# STAGE=test, so synthetic data can never land in a real environment by
# by accident (same guard pattern used in other projects' seeders).
#
# Run inside the backend devcontainer:
#   cd /app/batch && ./database/seeders/seed.sh [--historical-data N] [--sensor-readings N] [--sensors N] [--reset]
#   e.g. cd /app/batch && ./database/seeders/seed.sh --historical-data 10000 --sensor-readings 20000 --sensors 200 --reset
set -e

STAGE=$(aws secretsmanager describe-secret \
  --secret-id "/${DEPLOY_APP}-secrets/MongoCredentials" \
  --query "Tags[?Key=='STAGE'].Value" --output text)

if [ "$STAGE" != "dev" ] && [ "$STAGE" != "test" ]; then
  echo "Seeding skipped for '$STAGE' stage (only dev/test allowed)." >&2
  exit 1
fi

python3 -m database.seeders.seed_mongo "$@"
