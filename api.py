import json
import os
from fastapi import FastAPI, File, Depends, HTTPException, Query, UploadFile
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text, distinct
from database import Base, engine, SessionLocal, get_db
from models import Map
from geoalchemy2 import WKBElement
from shapely.wkb import loads as to_shape
from shapely.geometry import shape
from geoalchemy2.elements import WKBElement
from shapely.wkb import loads as wkb_loads

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI()

class GeoJSONFeature(BaseModel):
    type: str
    geometry: dict
    properties: dict

class GeoJSONFeatureCollection(BaseModel):
    type: str
    features: List[GeoJSONFeature]

@app.post("/maps/")
async def create_map(name: str, entity_name: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Crear un nuevo Mapa.
    """
    if file.content_type != "application/geo+json" and not file.filename.endswith(".geojson"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .geojson files are accepted.")

    try:
        contents = await file.read()
        geojson_data = json.loads(contents)

        if geojson_data.get("type") != "FeatureCollection":
            raise HTTPException(status_code=400, detail="The GeoJSON must be a FeatureCollection.")

        for feature in geojson_data["features"]:
            geometry = feature.get("geometry")
            properties = feature.get("properties", {})
            if not geometry:
                raise HTTPException(status_code=400, detail="Each feature must have a geometry.")

            geom_str = json.dumps(geometry)

            # Crear una nueva entrada en la base de datos
            mapa = Map(
                name=name,
                entity_name=entity_name,
                geom=None,  # Inicialmente None, se actualizará después
                properties=properties  # Guardar las propiedades
            )
            db.add(mapa)
            db.commit()
            db.refresh(mapa)

            # Actualizar el campo geom usando ST_GeomFromGeoJSON
            db.execute(text("UPDATE maps SET geom = ST_GeomFromGeoJSON(:geom) WHERE id = :id"), {"geom": geom_str, "id": mapa.id})
            db.commit()

        return {"message": "GeoJSON processed and saved successfully"}

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/maps/")
def get_maps(name: str, db: Session = Depends(get_db)):
    try:
        maps = db.query(Map).filter(Map.name == name).all()
        response_data = []
        for map_item in maps:
            geom = wkb_loads(bytes(map_item.geom.data)) if isinstance(map_item.geom, WKBElement) else None
            map_dict = {
                "id": map_item.id,
                "name": map_item.name,
                "entity_name": map_item.entity_name,
                "geom": geom.__geo_interface__ if geom else None,
                "properties": map_item.properties
            }
            response_data.append(map_dict)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/maps/names/")
def get_maps_names(db: Session = Depends(get_db)):
    try:
        names = db.query(distinct(Map.name)).all()
        unique_names = [name[0] for name in names]
        return unique_names
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/maps/")
def delete_map_by_name(name: str, db: Session = Depends(get_db)):
    """
    Eliminar un Mapa por su nombre.
    """
    try:
        maps_to_delete = db.query(Map).filter(Map.name == name).all()
        if not maps_to_delete:
            raise HTTPException(status_code=404, detail="Map not found")

        for map_item in maps_to_delete:
            db.delete(map_item)
        db.commit()

        return {"message": f"Map(s) with name '{name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()