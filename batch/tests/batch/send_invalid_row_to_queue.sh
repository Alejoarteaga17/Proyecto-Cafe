#!/bin/bash
# Demo script: sends a row with an invalid historical record directly to the
# coffee batch SQS queue, bypassing the normal historical ingestion path.
# ValidateAndPersist re-validates it, fails, and forwards it to the dead-letter
# queue itself -- this is how you can show that path without needing a malformed
# historical file to make it through the earlier stages.
#
# Run inside the backend devcontainer (needs the AWS CLI + credentials):
#   cd tests/batch && ./send_invalid_row_to_queue.sh
set -e

QUEUE_URL=$(aws ssm get-parameter \
  --name "/${DEPLOY_APP}-queue/CoffeeBatchQueueUrl" \
  --query 'Parameter.Value' \
  --output text)

MESSAGE_BODY='{"LON":-75.68,"LAT":4.53,"YEAR":2026,"MM":8,"DD":22,"DOY":234,"Date":"2026-08-22","Temp_Max":25.0,"Temp_Min":17.0,"Humidity":70.0,"Solar_Radiation":500.0,"Precipitation_mm":2.0,"Location":"Armenia","Close_USD_60kg":180.0,"Is_Weekend":false,"Is_Interpolated":false,"brl":5.0,"cny":7.0,"mxn":18.0,"invalid_field":true}'

aws sqs send-message \
  --queue-url "$QUEUE_URL" \
  --message-body "$MESSAGE_BODY"

echo "Message sent. The unexpected field should cause ValidateAndPersist to reject the row and forward it to the dead-letter queue -- check the DLQ alarm and its messages in the AWS console."
