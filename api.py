from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from database import Base, engine, SessionLocal
from models import Map

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
            if not geometry:
                raise HTTPException(status_code=400, detail="Each feature must have a geometry.")

            geom_str = json.dumps(geometry)

            # Crear una nueva entrada en la base de datos
            mapa = Map(
                name=name,
                entity_name=entity_name,
                geom=None  # Inicialmente None, se actualizará después
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
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

