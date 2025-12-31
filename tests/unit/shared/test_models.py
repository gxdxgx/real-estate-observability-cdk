import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from shared.database.models import Property, PropertyCreate, PropertyUpdate, PropertyStatus

class TestPropertyModels:
    """Test cases for property data models."""

    def test_property_create_valid_data(self, sample_property_data):
        """Test creating PropertyCreate with valid data."""
        # Act
        property_create = PropertyCreate(**sample_property_data)
        
        # Assert
        assert property_create.address == sample_property_data['address']
        assert property_create.price == sample_property_data['price']
        assert property_create.location == sample_property_data['location']
        assert property_create.property_type == sample_property_data['property_type']
        assert property_create.bedrooms == sample_property_data['bedrooms']
        assert property_create.bathrooms == sample_property_data['bathrooms']
        assert property_create.square_feet == sample_property_data['square_feet']
        assert property_create.description == sample_property_data['description']
        assert property_create.status == sample_property_data['status']

    def test_property_create_minimal_data(self):
        """Test creating PropertyCreate with minimal required data."""
        # Arrange
        minimal_data = {
            'address': '123 Main St',
            'price': Decimal('100000'),
            'location': 'Test City',
            'property_type': 'house'
        }
        
        # Act
        property_create = PropertyCreate(**minimal_data)
        
        # Assert
        assert property_create.address == minimal_data['address']
        assert property_create.price == minimal_data['price']
        assert property_create.location == minimal_data['location']
        assert property_create.property_type == minimal_data['property_type']
        assert property_create.status == PropertyStatus.ACTIVE  # Default value

    def test_property_create_validation_errors(self):
        """Test PropertyCreate validation with invalid data."""
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            PropertyCreate()
        
        # Test invalid price (negative)
        with pytest.raises(ValidationError):
            PropertyCreate(
                address='123 Main St',
                price=Decimal('-100'),
                location='Test City',
                property_type='house'
            )
        
        # Test invalid address (too short)
        with pytest.raises(ValidationError):
            PropertyCreate(
                address='123',
                price=Decimal('100000'),
                location='Test City',
                property_type='house'
            )
        
        # Test invalid status
        with pytest.raises(ValidationError):
            PropertyCreate(
                address='123 Main St',
                price=Decimal('100000'),
                location='Test City',
                property_type='house',
                status='invalid_status'
            )

    def test_property_create_with_decimal_conversion(self):
        """Test PropertyCreate with automatic decimal conversion."""
        # Arrange
        data = {
            'address': '123 Main St',
            'price': 100000.50,  # Float will be converted to Decimal
            'location': 'Test City',
            'property_type': 'house',
            'bathrooms': 2.5  # Float will be converted to Decimal
        }
        
        # Act
        property_create = PropertyCreate(**data)
        
        # Assert
        assert isinstance(property_create.price, Decimal)
        assert property_create.price == Decimal('100000.50')
        assert isinstance(property_create.bathrooms, Decimal)
        assert property_create.bathrooms == Decimal('2.5')

    def test_property_creation_from_property_create(self, sample_property_data):
        """Test creating Property from PropertyCreate."""
        # Arrange
        property_create = PropertyCreate(**sample_property_data)
        
        # Act
        property_obj = Property.create_new(property_create)
        
        # Assert
        assert property_obj.address == sample_property_data['address']
        assert property_obj.price == sample_property_data['price']
        assert property_obj.id is not None
        assert property_obj.created_at is not None
        assert property_obj.updated_at is not None
        assert property_obj.created_at == property_obj.updated_at

    def test_property_update_fields(self, sample_property_data):
        """Test updating property fields."""
        # Arrange
        property_create = PropertyCreate(**sample_property_data)
        property_obj = Property.create_new(property_create)
        original_updated_at = property_obj.updated_at
        
        # Act
        update_data = PropertyUpdate(price=Decimal('600000'), bedrooms=4)
        updated_property = property_obj.update_fields(update_data)
        
        # Assert
        assert updated_property.price == Decimal('600000')
        assert updated_property.bedrooms == 4
        assert updated_property.address == sample_property_data['address']  # Unchanged
        assert updated_property.updated_at != original_updated_at  # Should be updated

    def test_property_to_dynamodb_item(self, sample_property_data):
        """Test converting Property to DynamoDB item."""
        # Arrange
        property_create = PropertyCreate(**sample_property_data)
        property_obj = Property.create_new(property_create)
        
        # Act
        item = property_obj.to_dynamodb_item()
        
        # Assert
        assert isinstance(item, dict)
        assert item['id'] == property_obj.id
        assert item['address'] == property_obj.address
        assert item['price'] == property_obj.price
        assert item['created_at'] == property_obj.created_at
        assert item['updated_at'] == property_obj.updated_at

    def test_property_from_dynamodb_item(self, sample_property_data):
        """Test creating Property from DynamoDB item."""
        # Arrange
        property_create = PropertyCreate(**sample_property_data)
        original_property = Property.create_new(property_create)
        item = original_property.to_dynamodb_item()
        
        # Act
        restored_property = Property.from_dynamodb_item(item)
        
        # Assert
        assert restored_property.id == original_property.id
        assert restored_property.address == original_property.address
        assert restored_property.price == original_property.price
        assert restored_property.created_at == original_property.created_at
        assert restored_property.updated_at == original_property.updated_at

    def test_property_status_constants(self):
        """Test PropertyStatus constants."""
        assert PropertyStatus.ACTIVE == "active"
        assert PropertyStatus.SOLD == "sold"
        assert PropertyStatus.PENDING == "pending"
        assert PropertyStatus.OFF_MARKET == "off_market"