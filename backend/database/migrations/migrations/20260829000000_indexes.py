# pylint: disable=invalid-name
import os

from mongodb_migrations.base import BaseMigration
from pymongo import ASCENDING, DESCENDING

from src.common.mongo import get_collection

DEPLOY_APP = os.environ['DEPLOY_APP']
MONGO_CREDENTIALS_SECRET_NAME = f'/{DEPLOY_APP}-secrets/MongoCredentials'
INDEX = [('location', ASCENDING), ('Date', DESCENDING)]


class Migration(BaseMigration):
    """Speeds up historical coffee queries by location and date."""

    def upgrade(self):
        get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                       'coffeeHistoricalData').create_index(INDEX)
        print('Created location+Date index on coffeeHistoricalData.')

    def downgrade(self):
        get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                       'coffeeHistoricalData').drop_index(INDEX)
        print('Dropped location+Date index on coffeeHistoricalData.')
