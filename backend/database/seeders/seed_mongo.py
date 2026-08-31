"""Fills coffee historical data and coffee sensor readings with realistic synthetic data.

Run via database/seeders/seed.sh, not directly -- that wrapper refuses to run
outside dev/test.
"""
import argparse
import datetime as dt
import os
import random

from src.common.coffee_batch_validator import MAX_ROWS, validate_row
from src.common.coffee_rules import build_alert_summary, validate_coffee_reading
from src.common.mongo import get_collection

DEPLOY_APP = os.environ['DEPLOY_APP']
MONGO_CREDENTIALS_SECRET_NAME = f'/{DEPLOY_APP}-secrets/MongoCredentials'
HISTORICAL_DATA_COLLECTION = 'coffeeHistoricalData'
SENSOR_READINGS_COLLECTION = 'coffeeSensorReadings'
# A single insert_many() with tens of thousands of documents can outlast what
# an Atlas M0 (free tier) connection tolerates and gets dropped mid-request
# (pymongo.errors.AutoReconnect: connection closed). Batching avoids that and
# keeps memory use bounded regardless of how large --historical-data/
# --sensor-readings is.
INSERT_BATCH_SIZE = 500

COFFEE_LOCATIONS = {
    'Armenia': (-75.6811, 4.5339),
    'Manizales': (-75.5138, 5.0703),
    'Pereira': (-75.6946, 4.8143),
    'Medellín': (-75.5636, 6.2442),
}


def _random_recent_datetime(days_back):
    seconds_back = random.randint(0, days_back * 24 * 3600)
    return dt.datetime.now() - dt.timedelta(seconds=seconds_back)


def _utc_now_isoformat():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _build_historical_record(index):
    location = random.choice(list(COFFEE_LOCATIONS))
    lon, lat = COFFEE_LOCATIONS[location]
    date = _random_recent_datetime(365)
    temp_max = round(random.uniform(18, 28), 1)
    row = {
        'LON': round(lon + random.uniform(-0.05, 0.05), 5),
        'LAT': round(lat + random.uniform(-0.05, 0.05), 5),
        'YEAR': date.year,
        'MM': date.month,
        'DD': date.day,
        'DOY': date.timetuple().tm_yday,
        'Date': date.date().isoformat(),
        'Temp_Max': temp_max,
        'Temp_Min': round(random.uniform(12, temp_max), 1),
        'Humidity': round(random.uniform(60, 88), 1),
        'Solar_Radiation': round(random.uniform(200, 700), 1),
        'Precipitation_mm': round(random.uniform(0, 40), 1),
        'Location': location,
        'Close_USD_60kg': round(random.uniform(100, 250), 2),
        'Is_Weekend': date.weekday() >= 5,
        'Is_Interpolated': random.choice([True, False]),
        'brl': round(random.uniform(4, 6), 2),
        'cny': round(random.uniform(6, 8), 2),
        'mxn': round(random.uniform(16, 20), 2),
    }
    errors = validate_row(row)
    if errors:
        raise ValueError(f'Generated an invalid historical record: {errors}')

    document = dict(row)
    # SplitAndEnqueue adds these two to every real row, for traceability back
    # to the uploaded Excel file -- simulate batches of up to MAX_ROWS rows
    # so seeded documents carry them too, instead of silently omitting them.
    document['source_s3_key'] = f'processed/seed-batch-{index // MAX_ROWS}.xlsx'
    document['row_number'] = (index % MAX_ROWS) + 1
    now = _utc_now_isoformat()
    document['created_at'] = now
    document['updated_at'] = now
    return document


def _build_sensor_reading(sensor_id, location):
    reading = {
        'sensor_id': sensor_id,
        'location': location,
        'timestamp': _random_recent_datetime(14).isoformat(),
        'Temp_Max': round(random.uniform(18, 32), 1),
        'Temp_Min': round(random.uniform(12, 20), 1),
        'Humidity': round(random.uniform(60, 95), 1),
        'Solar_Radiation': round(random.uniform(200, 700), 1),
        'Precipitation_mm': round(random.uniform(0, 40), 1),
        'soil_ph': round(random.uniform(4.5, 7), 2),
        'soil_moisture': round(random.uniform(35, 90), 1),
        'nutrients_mg_kg': {
            'N': round(random.uniform(20, 60), 1),
            'P': round(random.uniform(8, 25), 1),
            'K': round(random.uniform(70, 150), 1),
        },
    }
    errors = validate_coffee_reading(reading)
    if errors:
        raise ValueError(f'Generated an invalid sensor reading: {errors}')

    document = dict(reading)
    alert_summary = build_alert_summary(reading)
    if alert_summary['status'] == 'alert':
        document['alert_summary'] = alert_summary
    now = _utc_now_isoformat()
    document['created_at'] = now
    document['updated_at'] = now
    return document


def _insert_in_batches(collection, documents):
    inserted = 0
    batch = []
    for document in documents:
        batch.append(document)
        if len(batch) >= INSERT_BATCH_SIZE:
            collection.insert_many(batch)
            inserted += len(batch)
            batch = []
    if batch:
        collection.insert_many(batch)
        inserted += len(batch)
    return inserted


def seed_historical_data(count):
    collection = get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                                HISTORICAL_DATA_COLLECTION)
    documents = (_build_historical_record(i) for i in range(count))
    return _insert_in_batches(collection, documents)


def seed_sensor_readings(count, sensor_count):
    sensor_ids = [f'sensor-{i:03d}' for i in range(1, sensor_count + 1)]
    collection = get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                                SENSOR_READINGS_COLLECTION)
    documents = (_build_sensor_reading(random.choice(sensor_ids),
                                       random.choice(list(COFFEE_LOCATIONS)))
                 for _ in range(count))
    return _insert_in_batches(collection, documents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--historical-data', type=int, default=500)
    parser.add_argument('--sensor-readings', type=int, default=3000)
    parser.add_argument('--sensors', type=int, default=5)
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Delete all existing documents in both collections first')
    args = parser.parse_args()

    if args.reset:
        for name in (HISTORICAL_DATA_COLLECTION, SENSOR_READINGS_COLLECTION):
            deleted = get_collection(MONGO_CREDENTIALS_SECRET_NAME,
                                     name).delete_many({}).deleted_count
            print(f'Deleted {deleted} existing documents from {name}.')

    reports_inserted = seed_historical_data(args.historical_data)
    readings_inserted = seed_sensor_readings(args.sensor_readings, args.sensors)

    print(f'Inserted {reports_inserted} documents into '
          f'{HISTORICAL_DATA_COLLECTION}.')
    print(f'Inserted {readings_inserted} documents into '
          f'{SENSOR_READINGS_COLLECTION} across {args.sensors} sensors.')


if __name__ == '__main__':
    main()
