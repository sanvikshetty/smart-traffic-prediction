from datetime import datetime
from pydantic import BaseModel, Field

class TrafficReadingIn(BaseModel):
    sensor_id: str = Field(min_length=1, max_length=20)
    vehicle_count: int = Field(ge=0)
    average_speed: float = Field(ge=0)
    occupancy: float = Field(ge=0, le=1)
    congestion_level: str = Field(pattern='^(LOW|MEDIUM|HIGH|SEVERE)$')

class PredictionOut(BaseModel):
    sensor_id: str
    generated_at: datetime
    target_time: datetime
    horizon_minutes: int
    predicted_volume: float
    predicted_speed: float | None
    predicted_congestion: str
    model_name: str
