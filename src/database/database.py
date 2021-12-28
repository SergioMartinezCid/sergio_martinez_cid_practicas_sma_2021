import json
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from const import DB_CREDENTIALS_FILE, DEFAULT_JOKES_FILE
from functionality import Functionality
from .base import Base
from .functionality_regex import FunctionalityRegex
from .base_url import BaseUrl
from .joke import Joke

class Database:
    default_base_urls = [
        {'id': 'SEARCH_PEOPLE_URL', 'url': 'https://en.wikipedia.org/w/index.php'},
        {'id': 'SEARCH_GIFS_URL', 'url': 'https://g.tenor.com/v1/search'}]

    default_functionality_regex = [
        {'regex': r'\s*what\s+can\s+you\s+do\s*\??\s*$',
            'functionality': Functionality.SEND_FUNCTIONALITY},
        {'regex': r'\s*show\s+me\s+the\s+time\s*$', 'functionality': Functionality.SHOW_TIME},
        {'regex': r'\s*who\s+is\s+(\S.*?)\s*\??\s*$',
            'functionality': Functionality.SEARCH_PERSON_INFO},
        {'regex': r'\s*(?:create|make)\s+file\s+\'(\S.*)\'\s*$',
            'functionality': Functionality.MAKE_FILE},
        {'regex': r'\s*download\s+gifs\s+(?:about|of)\s+(\S.*)\s*$',
            'functionality': Functionality.DOWNLOAD_GIFS},
        {'regex': r'\s*tell\s+(?:me\s)?\s*a\s+joke\s*$', 'functionality': Functionality.TELL_JOKE},
        {'regex': r'\s*exit\s*$', 'functionality': Functionality.SEND_EXIT}]

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
                session.bulk_insert_mappings(BaseUrl, self.default_base_urls)
                session.commit()
            except IntegrityError:
                session.rollback()

            # Seed functionality to regex
            try:
                session.bulk_insert_mappings(FunctionalityRegex, self.default_functionality_regex)
                session.commit()
            except IntegrityError:
                session.rollback()

            # Seed jokes
            try:
                with open(DEFAULT_JOKES_FILE, 'r', encoding='utf-8') as joke_file:
                    joke_mappings = map(lambda joke: {'joke': joke.strip()}, joke_file.readlines())
                    session.bulk_insert_mappings(Joke, joke_mappings)
                session.commit()
            except IntegrityError:
                session.rollback()

    def get_new_session(self):
        return Session(self.engine)

db = Database()
