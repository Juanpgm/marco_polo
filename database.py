from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://jpgm:Sakura13@localhost:5432/maps"

# Crear el motor de conexión
engine = create_engine(DATABASE_URL)

# Crear la base de modelos
Base = declarative_base()

# Crear el objeto de sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()