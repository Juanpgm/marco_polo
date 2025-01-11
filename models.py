from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from database import Base
from pydantic import BaseModel, Field, ConfigDict

class Map(BaseModel):
    id: int
    name: str
    geom: Geometry

    class Config:
        arbitrary_types_allowed = True

class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    entity_name = Column(String, index=True)
    geom = Column(Geometry('GEOMETRY', srid=4326))