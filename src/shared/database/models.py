import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from decimal import Decimal

class PropertyStatus:
    """Property status constants."""
    ACTIVE = "active"
    SOLD = "sold"
    PENDING = "pending"
    OFF_MARKET = "off_market"

class PropertyBase(BaseModel):
    """Base property model for validation."""
    address: str = Field(..., min_length=5, max_length=500)
    price: Decimal = Field(..., gt=0)
    location: str = Field(..., min_length=2, max_length=100)
    property_type: str = Field(..., min_length=2, max_length=50)
    bedrooms: Optional[int] = Field(None, ge=0, le=20)
    bathrooms: Optional[Decimal] = Field(None, ge=0, le=10)
    square_feet: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field(default=PropertyStatus.ACTIVE)
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = [
            PropertyStatus.ACTIVE, 
            PropertyStatus.SOLD, 
            PropertyStatus.PENDING, 
            PropertyStatus.OFF_MARKET
        ]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v
    
    @validator('price', 'bathrooms', pre=True)
    def convert_to_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v

class PropertyCreate(PropertyBase):
    """Property creation model."""
    pass

class PropertyUpdate(BaseModel):
    """Property update model - all fields optional."""
    address: Optional[str] = Field(None, min_length=5, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    property_type: Optional[str] = Field(None, min_length=2, max_length=50)
    bedrooms: Optional[int] = Field(None, ge=0, le=20)
    bathrooms: Optional[Decimal] = Field(None, ge=0, le=10)
    square_feet: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = [
                PropertyStatus.ACTIVE, 
                PropertyStatus.SOLD, 
                PropertyStatus.PENDING, 
                PropertyStatus.OFF_MARKET
            ]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {valid_statuses}')
        return v
    
    @validator('price', 'bathrooms', pre=True)
    def convert_to_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v

class Property(PropertyBase):
    """Full property model with system fields."""
    id: str
    created_at: str
    updated_at: str
    
    @classmethod
    def create_new(cls, property_data: PropertyCreate) -> 'Property':
        """Create a new property with system fields."""
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            **property_data.dict()
        )
    
    def update_fields(self, update_data: PropertyUpdate) -> 'Property':
        """Update property with new data."""
        update_dict = update_data.dict(exclude_unset=True)
        if update_dict:
            update_dict['updated_at'] = datetime.now().isoformat()
            
            # Update the current instance
            for key, value in update_dict.items():
                setattr(self, key, value)
        
        return self
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format."""
        return self.dict()
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'Property':
        """Create Property instance from DynamoDB item."""
        return cls(**item)