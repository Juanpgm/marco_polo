from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Map(BaseModel):
    mapa_name: str
    data: bool = False

maps = []

@app.get("/")
def root():
    return {"message": "Disconnected from the server"}

@app.post("/maps")
def create_map(mapa:Map):
    maps.append(mapa)
    return maps

@app.get("/maps", response_model=list[Map])
def list_maps(limit: int = 10):
    return maps[0:limit]

@app.get("/maps/{map_id}", response_model=Map)
def read_map(map_id: int) -> Map:
    if map_id < len(maps):
        return maps[map_id]
    else:
        raise HTTPException(status_code=404, 
                            detail=f"Mapa con el código: {map_id}, NO disponible en Base de Datos")
    