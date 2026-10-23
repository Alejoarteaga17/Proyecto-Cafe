# pylint: disable=invalid-name
import os

from mongodb_migrations.base import BaseMigration
from pymongo import ASCENDING, DESCENDING

from src.common.mongo import get_collection

DEPLOY_APP = os.environ['DEPLOY_APP']
MONGO_CREDENTIALS_SECRET_NAME = f'/{DEPLOY_APP}-secrets/MongoCredentials'
INDEX = [('source.device_id', ASCENDING), ('temporal.date', DESCENDING)]


class Migration(BaseMigration):
    """Speeds up streaming telemetry queries by device and date."""

    def upgrade(self):
        get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                       'coffee_measurements').create_index(INDEX)
        print('Created device+date index on coffee_measurements.')

    def downgrade(self):
        get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                       'coffee_measurements').drop_index(INDEX)
        print('Dropped device+date index on coffee_measurements.')
