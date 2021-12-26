from sqlalchemy import Column, String, Enum
from functionality import Functionality
from .base import Base

class FunctionalityRegex(Base):
    __tablename__ = "functionality_regex"

    id  = Column(String, primary_key=True)
    regex = Column(String, unique=True)
    functionality = Column(Enum(Functionality), nullable=False)

    def __repr__(self) -> str:
        return f'BaseUrl(id={self.id!r}, url={self.url!r})'
