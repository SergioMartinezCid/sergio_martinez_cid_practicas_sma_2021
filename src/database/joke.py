from sqlalchemy import Column, String
from sqlalchemy.sql.sqltypes import Boolean
from .base import Base

class Joke(Base):
    __tablename__ = "joke"

    joke = Column(String, primary_key=True)
    is_new = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return f'Joke(joke={self.url!r})'
