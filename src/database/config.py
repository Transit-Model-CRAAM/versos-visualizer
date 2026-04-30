import pathlib
from sqlalchemy.orm import declarative_base

Base = declarative_base()
DB_PATH = pathlib.Path("database/VERSOS_logs.db")
EVENTS_DATA_DIR = pathlib.Path("database/events")