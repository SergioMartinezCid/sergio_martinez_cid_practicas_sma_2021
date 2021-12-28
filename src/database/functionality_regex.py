from sqlalchemy import Column, String, Enum
from functionality import Functionality
from .base import Base

class FunctionalityRegex(Base):
    __tablename__ = "functionality_regex"

    regex = Column(String, primary_key=True)
    functionality = Column(Enum(Functionality), nullable=False)

    def __repr__(self) -> str:
        return f'FunctionalityRegex(regex={self.url!r}), functionality={self.functionality!r}'
