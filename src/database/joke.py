from sqlalchemy import Column, String
from sqlalchemy.sql.sqltypes import Integer
from .base import Base

class Joke(Base):
    __tablename__ = "joke"

    id  = Column(Integer, primary_key=True, autoincrement=True)
    joke = Column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f'Joke(id={self.id!r}, joke={self.url!r})'
