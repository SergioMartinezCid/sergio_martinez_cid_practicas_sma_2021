from sqlalchemy import Column, String
from .database import db

class Joke(db.base):
    __tablename__ = "joke"

    id  = Column(String, primary_key=True)
    joke = Column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f'Joke(id={self.id!r}, joke={self.url!r})'
