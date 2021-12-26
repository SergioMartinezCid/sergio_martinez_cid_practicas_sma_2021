import json
from sqlalchemy import create_engine
from const import DB_CREDENTIALS_FILE
from .base import Base

with open(DB_CREDENTIALS_FILE, 'r', encoding='utf-8') as db_credentials_file:
    db_creedentials = json.load(db_credentials_file)

CONNECTION_URL = ('postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOSTNAME}' + \
    ':{POSTGRES_PORT}/{POSTGRES_DB}').format(**db_creedentials)
engine = create_engine(CONNECTION_URL, future=True)

def initialize_database():
    Base.metadata.create_all(engine, checkfirst=True)
