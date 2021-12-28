import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base
from const import DB_CREDENTIALS_FILE

class Database:
    def __init__(self) -> None:
        self.engine = None
        self.base = declarative_base()

    def initialize_connection(self):
        with open(DB_CREDENTIALS_FILE, 'r', encoding='utf-8') as db_credentials_file:
            db_creedentials = json.load(db_credentials_file)
        connection_url = ('postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOSTNAME}' + \
            ':{POSTGRES_PORT}/{POSTGRES_DB}').format(**db_creedentials)

        self.engine = create_engine(connection_url, future=True)
        self.base.metadata.create_all(self.engine, checkfirst=True)

    def get_new_session(self):
        return Session(self.engine)

db = Database()
