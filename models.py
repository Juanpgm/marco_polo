from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()

class Map(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    entity_name = Column(String, index=True)
    geom = Column(Geometry('GEOMETRY', srid=4326))
    properties = Column(JSON)  # Nueva columna para almacenar las propiedades

'''class Geometry(BaseModel):
    type: str
    coordinates: List

class Properties(BaseModel):
    # Define aquí las propiedades que esperas en el GeoJSON
    name: Optional[str] = None
    # Agrega más campos según sea necesario

class Feature(BaseModel):
    type: str
    geometry: Geometry
    properties: Properties

class FeatureCollection(BaseModel):
    type: str
    features: List[Feature]'''