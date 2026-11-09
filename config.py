import os
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', '')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DATABASE_NAME = 'todoapp'

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is not None:
        return _db
    if not MONGODB_URI or '<username>' in MONGODB_URI or 'xxxxx' in MONGODB_URI:
        raise ConfigurationError(
            'MongoDB URI not configured. Update the .env file with your MongoDB Atlas connection string.'
        )
    _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    _db = _client[DATABASE_NAME]
    return _db


def get_collection(name):
    return get_db()[name]


def check_connection():
    try:
        db = get_db()
        db.client.admin.command('ping')
        return True
    except Exception:
        return False
