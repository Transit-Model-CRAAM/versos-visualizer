import uuid

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.database.config import Base

class Day(Base):
    __tablename__ = 'days'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date_str = Column(String, unique=True, nullable=False)
    configs = relationship("InputConfig", back_populates="day")

class InputConfig(Base):
    __tablename__ = 'input_configs'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    day_id = Column(String(36), ForeignKey('days.id'))
    config_hash = Column(String, nullable=False, index=True)
    
    # Parâmetros agora como colunas reais para fácil detecção e consulta
    data_select = Column(String)
    interpolation_select = Column(String)
    smooth_window = Column(Integer)
    n_apply_smooth = Column(Integer)
    diff_std = Column(Float)
    number_of_segments = Column(Integer)
    quantity_mean_std = Column(Float)
    merge_gap = Column(Float)
    relative_height = Column(Float)
    avoid_border = Column(Integer)
    min_curves = Column(Integer)
    dtw_weight = Column(Float)
    
    day = relationship("Day", back_populates="configs")
    events = relationship("EventMetadata", back_populates="config")

class EventMetadata(Base):
    __tablename__ = 'events_metadata'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(36), ForeignKey('input_configs.id'))
    start_time = Column(String)
    end_time = Column(String)
    curve_select = Column(Integer)
    offset = Column(Float)
    is_automatic = Column(Boolean)
    is_edited = Column(Boolean)
    is_valid = Column(Boolean)
    numeric_data_path = Column(String)

    config = relationship("InputConfig", back_populates="events")