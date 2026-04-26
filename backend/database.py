from sqlmodel import SQLModel, create_engine, Session
from models.user import User  # noqa: F401 — ensure table is registered
from models.pipeline import Pipeline, PipelineRun  # noqa: F401 — ensure tables are registered

DATABASE_URL = "sqlite:////data/nimbus.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
