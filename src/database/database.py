import json
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from const import DB_CREDENTIALS_FILE
from .default_data import get_answers, get_default_base_urls, \
    get_default_functionality_regex, get_default_jokes
from .base import Base
from .answer import Answer
from .functionality_regex import FunctionalityRegex
from .base_url import BaseUrl
from .joke import Joke

class Database:
    def __init__(self) -> None:
        self.engine = None
        self.base = Base

    def initialize_connection(self):
        with open(DB_CREDENTIALS_FILE, 'r', encoding='utf-8') as db_credentials_file:
            db_creedentials = json.load(db_credentials_file)
        connection_url = ('postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOSTNAME}' + \
            ':{POSTGRES_PORT}/{POSTGRES_DB}').format(**db_creedentials)

        self.engine = create_engine(connection_url, future=True)
        self.base.metadata.create_all(self.engine, checkfirst=True)

    # Seeds default data to the database
    # When there is an error it means the data already existed and
    # the transaction is rolled back
    def seed_data(self):
        with self.get_new_session() as session:
            session: Session # Type notation
            # Seed base urls
            try:
                session.bulk_insert_mappings(BaseUrl, get_default_base_urls())
                session.commit()
            except IntegrityError:
                session.rollback()

            # Seed functionality to regex
            try:
                session.bulk_insert_mappings(FunctionalityRegex, get_default_functionality_regex())
                session.commit()
            except IntegrityError:
                session.rollback()
            
            # Seed answers
            try:
                session.bulk_insert_mappings(Answer, get_answers())
                session.commit()
            except IntegrityError:
                session.rollback()

            # Seed jokes
            try:
                session.bulk_insert_mappings(Joke, get_default_jokes())
                session.commit()
            except IntegrityError:
                session.rollback()

    def get_new_session(self):
        return Session(self.engine)

db = Database()
