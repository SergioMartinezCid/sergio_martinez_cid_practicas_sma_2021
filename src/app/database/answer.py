from sqlalchemy import Column, String
from .base import Base

class Answer(Base):
    __tablename__ = "answer"

    id  = Column(String, primary_key=True)
    text = Column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f'Answer(id={self.id!r}, text={self.text!r})'
