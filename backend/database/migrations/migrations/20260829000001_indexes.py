# pylint: disable=invalid-name
import os

from mongodb_migrations.base import BaseMigration
from pymongo import ASCENDING, DESCENDING

from src.common.mongo import get_collection

DEPLOY_APP = os.environ['DEPLOY_APP']
MONGO_CREDENTIALS_SECRET_NAME = f'/{DEPLOY_APP}-secrets/MongoCredentials'
INDEX = [('sensor_id', ASCENDING), ('timestamp', DESCENDING)]


class Migration(BaseMigration):
    """Speeds up sensor telemetry queries by sensor and time."""

    def upgrade(self):
        get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                       'coffeeSensorReadings').create_index(INDEX)
        print('Created sensor_id+timestamp index on coffeeSensorReadings.')

    def downgrade(self):
        get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                       'coffeeSensorReadings').drop_index(INDEX)
        print('Dropped sensor_id+timestamp index on coffeeSensorReadings.')
