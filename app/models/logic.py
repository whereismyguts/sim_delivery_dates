from app.models.declarative import AppDecBase
from app_utils.db_utils.models import jsonb_property, BaseModel
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
import datetime


class RealModel(BaseModel, AppDecBase):
    __tablename__ = "region_delivery_schedule"

    id = Column(Integer, primary_key=True)

    region_id = Column(Integer, index=True)  # OKATO
    subject_name = Column(String, index=True)  # city

    default_delivery_price = Column(Integer, default=300)

    created = Column(DateTime, default=datetime.datetime.utcnow)
    deleted = Column(DateTime)

    holidays = Column(String)  # 31.12.2020,07.01.2021

    time_slots_weekend = Column(String)  # 10:00-12:00,13:00-17:00
    time_slots_workdays = Column(String)  # 10:00-12:00,13:00-17:00

    special_time_slots = Column(String)  # 03.01.2021 / 11:00-14:00, 15:00-17:00; 03.01.2021 / 17:00-19:00

    data = Column(JSONB)
