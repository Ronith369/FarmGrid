from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    phone = Column(String(30))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(40), default="farmer", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)
    farms = relationship("Farm", back_populates="farmer")
    resources = relationship("Resource", back_populates="owner")


class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(120), nullable=False)
    location = Column(String(200), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    land_size_acres = Column(Float, nullable=False)
    soil_type = Column(String(80))
    soil_color = Column(String(80))
    moisture = Column(Float)
    water_availability = Column(Float)
    previous_crop = Column(String(100))
    previous_yield = Column(Float)
    farmer = relationship("User", back_populates="farms")


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(120), nullable=False)
    resource_type = Column(String(80), nullable=False)
    specifications = Column(Text)
    location = Column(String(200), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    operating_from = Column(DateTime, nullable=False)
    operating_until = Column(DateTime, nullable=False)
    maintenance_status = Column(String(30), default="operational")
    status = Column(String(30), default="available")
    owner = relationship("User", back_populates="resources")
    bookings = relationship("Booking", back_populates="resource")


class ResourceRequest(Base):
    __tablename__ = "resource_requests"
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    resource_type = Column(String(80), nullable=False)
    requested_resource_id = Column(Integer, ForeignKey("resources.id"))
    earliest_start = Column(DateTime, nullable=False)
    latest_end = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    crop = Column(String(100), nullable=False)
    crop_stage = Column(String(100), nullable=False)
    urgency_score = Column(Integer, default=0)
    weather_risk_score = Column(Integer, default=0)
    crop_readiness_score = Column(Integer, default=0)
    logistics_score = Column(Integer, default=0)
    resource_constraints_score = Column(Integer, default=0)
    waiting_score = Column(Integer, default=0)
    status = Column(String(30), default="pending")
    created_at = Column(DateTime, default=now)
    farmer = relationship("User")
    farm = relationship("Farm")
    requested_resource = relationship("Resource")
    booking = relationship("Booking", back_populates="request", uselist=False)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("resource_requests.id"), unique=True, nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    buffer_minutes = Column(Integer, default=30)
    transit_minutes = Column(Integer, default=0)
    status = Column(String(30), default="confirmed")
    created_at = Column(DateTime, default=now)
    request = relationship("ResourceRequest", back_populates="booking")
    resource = relationship("Resource", back_populates="bookings")
    farmer = relationship("User")


class Disruption(Base):
    __tablename__ = "disruptions"
    id = Column(Integer, primary_key=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    reason = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)
    resource = relationship("Resource")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(160), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(60), default="general")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


class WeatherRecord(Base):
    __tablename__ = "weather_records"
    id = Column(Integer, primary_key=True)
    location = Column(String(200), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    sunlight = Column(Float)
    weather_condition = Column(String(100))
    source = Column(String(80), default="demo")
    observed_at = Column(DateTime, default=now)


class LabourProvider(Base):
    __tablename__ = "labour_providers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider_type = Column(String(30), nullable=False)
    name = Column(String(160), nullable=False)
    region = Column(String(160), nullable=False)
    workers_available = Column(Integer, default=0)
    skills = Column(Text)
    daily_wage_per_worker = Column(Float, nullable=False)
    available_from = Column(DateTime)
    available_until = Column(DateTime)
    is_active = Column(Boolean, default=True)


class LabourRequest(Base):
    __tablename__ = "labour_requests"
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    work_type = Column(String(100), nullable=False)
    workers_required = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    duration_days = Column(Integer, nullable=False)
    region = Column(String(160), nullable=False)
    urgency = Column(Integer, default=0)
    preferred_provider_type = Column(String(30))
    status = Column(String(30), default="open")
    notes = Column(Text, nullable=True)
    contractor_notes = Column(Text, nullable=True)
    accepted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=now)

    farmer = relationship("User", foreign_keys=[farmer_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])


class LabourOffer(Base):
    __tablename__ = "labour_offers"
    id = Column(Integer, primary_key=True)
    labour_request_id = Column(Integer, ForeignKey("labour_requests.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("labour_providers.id"), nullable=False)
    offered_workers = Column(Integer, nullable=False)
    wage_per_worker_day = Column(Float, nullable=False)
    status = Column(String(30), default="pending")
    created_at = Column(DateTime, default=now)


class MarketOrder(Base):
    __tablename__ = "market_orders"
    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop = Column(String(100), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    quality_grade = Column(String(30), nullable=False)
    required_date = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=False)
    offered_price_per_kg = Column(Float)
    status = Column(String(30), default="open")
    created_at = Column(DateTime, default=now)


class YieldOffer(Base):
    __tablename__ = "yield_offers"
    id = Column(Integer, primary_key=True)
    market_order_id = Column(Integer, ForeignKey("market_orders.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    action = Column(String(20), nullable=False)
    status = Column(String(30), default="submitted")
    created_at = Column(DateTime, default=now)


class FertilizerRecommendation(Base):
    __tablename__ = "fertilizer_recommendations"
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("users.id"))
    farm_id = Column(Integer, ForeignKey("farms.id"))
    crop = Column(String(100), nullable=False)
    preferred_fertilizer = Column(String(120))
    predicted_fertilizer = Column(String(120))
    suitability_score = Column(Float)
    model_used = Column(Boolean, default=False)
    explanation = Column(Text)
    created_at = Column(DateTime, default=now)


class PesticideRecommendation(Base):
    __tablename__ = "pesticide_recommendations"
    id = Column(Integer, primary_key=True)
    farmer_id = Column(Integer, ForeignKey("users.id"))
    farm_id = Column(Integer, ForeignKey("farms.id"))
    crop = Column(String(100), nullable=False)
    pest = Column(String(100), nullable=False)
    predicted_pesticide = Column(String(120))
    pest_pressure_score = Column(Float)
    model_used = Column(Boolean, default=False)
    explanation = Column(Text)
    created_at = Column(DateTime, default=now)


class OfflineSyncItem(Base):
    __tablename__ = "offline_sync_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(String(120), unique=True, nullable=False)
    action_type = Column(String(80), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(30), default="queued")
    created_at = Column(DateTime, default=now)
    synced_at = Column(DateTime)
