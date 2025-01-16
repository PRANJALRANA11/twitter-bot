import psycopg2
DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "sfr92KxlUDIc",
    "host": "ep-winter-cake-a5szakvz-pooler.us-east-2.aws.neon.tech",
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)