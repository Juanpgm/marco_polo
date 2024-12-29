from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String
from contextlib import asynccontextmanager

DATABASE_URL = "postgresql+asyncpg://jpgm:Sakura13@localhost:5432/master"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

class Map(Base):
    __tablename__ = "maps"
    id = Column(Integer, primary_key=True, index=True)
    mapa_name = Column(String, index=True)
    entity_name = Column(String)
    data = Column(Geometry("POLYGON"))

class MapCreate(BaseModel):
    mapa_name: str
    data: str  # GeoJSON string

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.post("/maps", response_model=MapCreate)
async def create_mapa(mapa: MapCreate, db: AsyncSession = Depends(get_db)):
    db_mapa = Map(mapa_name=mapa.mapa_name, data=mapa.data)
    db.add(db_mapa)
    await db.commit()
    await db.refresh(db_mapa)
    return db_mapa

@app.get("/maps", response_model=list[MapCreate])
async def list_mapas(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Map).limit(limit))
    mapas = result.scalars().all()
    return mapas

@app.get("/maps/{mapa_id}", response_model=MapCreate)
async def read_mapa(mapa_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Map).filter(Map.id == mapa_id))
    mapa = result.scalar_one_or_none()
    if mapa is None:
        raise HTTPException(status_code=404, detail=f"Mapa con el código: {mapa_id}, NO disponible en Base de Datos")
    return mapa