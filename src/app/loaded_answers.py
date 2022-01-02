import logging
from sqlalchemy.sql.expression import select
from .database import db, Answer

class LoadedAnswers:
    def __init__(self) -> None:
        self._answers = dict()

    def load_answers_from_database(self):
        with db.get_new_session() as session:
            answers = session.execute(select(Answer)).all()
            for answer in answers:
                self._answers[answer[0].id] = answer[0].text

    def __getitem__(self, key):
        if key in self._answers:
            return self._answers[key]
        logging.error('Key of answer not found')
        return 'SAMPLE TEXT'

loaded_answers = LoadedAnswers()
