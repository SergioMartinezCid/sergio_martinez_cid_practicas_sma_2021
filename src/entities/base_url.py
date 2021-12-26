from sqlalchemy import Column, String
from .base import Base

class BaseUrl(Base):
    __tablename__ = "base_url"

    id  = Column(String, primary_key=True)
    url = Column(String, unique=True, nullable=False)

    def __repr__(self) -> str:
        return f'BaseUrl(id={self.id!r}, url={self.url!r})'
