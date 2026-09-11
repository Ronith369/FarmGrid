from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    role: str = "farmer"


class FarmCreate(BaseModel):
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    land_size_acres: float = Field(gt=0)
    soil_type: Optional[str] = None
    soil_color: Optional[str] = None
    moisture: Optional[float] = Field(default=None, ge=0, le=100)
    water_availability: Optional[float] = Field(default=None, ge=0, le=100)
    previous_crop: Optional[str] = None
    previous_yield: Optional[float] = Field(default=None, ge=0)


class ResourceCreate(BaseModel):
    name: str
    resource_type: str
    specifications: Optional[str] = None
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    operating_from: datetime
    operating_until: datetime
    maintenance_status: str = "operational"
    status: str = "available"


class ResourceRequestCreate(BaseModel):
    farm_id: Optional[int] = None
    resource_type: str
    requested_resource_id: Optional[int] = None
    earliest_start: datetime
    latest_end: datetime
    duration_minutes: int = Field(gt=0)
    crop: str
    crop_stage: str
    urgency_score: int = Field(ge=0, le=25)
    weather_risk_score: int = Field(ge=0, le=25)
    crop_readiness_score: int = Field(ge=0, le=20)
    logistics_score: int = Field(ge=0, le=10)
    resource_constraints_score: int = Field(ge=0, le=5)


class DisruptionCreate(BaseModel):
    resource_id: int
    reason: str
    start_time: datetime
    end_time: Optional[datetime] = None


class LabourProviderCreate(BaseModel):
    provider_type: str
    name: str
    region: str
    workers_available: int = Field(ge=0)
    skills: Optional[str] = None
    daily_wage_per_worker: float = Field(gt=0)
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None


class LabourRequestCreate(BaseModel):
    work_type: str
    workers_required: int = Field(gt=0)
    start_date: datetime
    duration_days: int = Field(gt=0)
    region: str
    urgency: int = Field(ge=0, le=10)
    preferred_provider_type: Optional[str] = None


class LabourOfferCreate(BaseModel):
    labour_request_id: int
    provider_id: int
    offered_workers: int = Field(gt=0)
    wage_per_worker_day: float = Field(gt=0)


class MarketOrderCreate(BaseModel):
    crop: str
    quantity_kg: float = Field(gt=0)
    quality_grade: str
    required_date: datetime
    location: str
    offered_price_per_kg: Optional[float] = Field(default=None, gt=0)


class YieldResponseCreate(BaseModel):
    quantity_kg: float = Field(gt=0)
    action: str


class FertilizerRequest(BaseModel):
    farm_id: Optional[int] = None
    location: str
    crop: str
    soil_type: str
    soil_color: str
    moisture: float = Field(ge=0, le=100)
    water_availability: float = Field(ge=0, le=100)
    previous_crop: str
    previous_yield: float = Field(ge=0)
    preferred_fertilizer: Optional[str] = None


class PesticideRequest(BaseModel):
    farm_id: Optional[int] = None
    location: str
    crop: str
    crop_age_days: int = Field(ge=0)
    pest: str
    temperature: float
    humidity: float = Field(ge=0, le=100)
    rainfall: float = Field(ge=0)
    sunlight: float = Field(ge=0)
    observed_severity: float = Field(ge=0, le=100)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
