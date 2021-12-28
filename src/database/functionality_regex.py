from sqlalchemy import Column, String, Enum
from sqlalchemy.sql.sqltypes import Integer
from functionality import Functionality
from .base import Base

class FunctionalityRegex(Base):
    __tablename__ = "functionality_regex"

    id  = Column(Integer, primary_key=True, autoincrement=True)
    regex = Column(String, unique=True)
    functionality = Column(Enum(Functionality), nullable=False)

    def __repr__(self) -> str:
        return f'FunctionalityRegex(id={self.id!r}, regex={self.url!r}), ' + \
            'functionality={self.functionality!r}'
