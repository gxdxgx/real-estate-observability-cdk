import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from handlers.api.calculate.cash_flow import handler, CashFlowRequest

class TestCashFlow:
    """Test cases for cash flow calculation handler."""

    def test_cash_flow_calculation_success(self, api_gateway_event, lambda_context):
        """Test successful cash flow calculation."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'path': '/api/v1/calculate/cash-flow',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 40000000,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 5,
                'management_fee_rate': 6,
                'insurance_monthly': 50000,
                'maintenance_monthly': 100000,
                'common_area_utilities_monthly': 30000,
                'tax_rate': 20
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'data' in body
        
        data = body['data']
        assert 'noi' in data
        assert 'btcf' in data
        assert 'atcf' in data
        assert 'monthly_noi' in data
        assert 'monthly_btcf' in data
        assert 'monthly_atcf' in data
        assert 'annual_loan_payment' in data
        assert 'monthly_loan_payment' in data
        assert 'annual_tax' in data
        assert 'breakdown' in data
        
        # Verify calculations are positive numbers
        assert isinstance(data['noi'], (int, float))
        assert isinstance(data['btcf'], (int, float))
        assert isinstance(data['atcf'], (int, float))

    def test_cash_flow_minimal_input(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with minimal required inputs."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 10000000,
                'loan_amount': 8000000,
                'loan_term_years': 20,
                'interest_rate': 3.0,
                'monthly_rent': 100000,
                'unit_count': 5,
                'vacancy_rate': 3
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'data' in body

    def test_cash_flow_zero_loan(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with zero loan amount."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 0,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 5,
                'management_fee_rate': 6,
                'insurance_monthly': 50000,
                'maintenance_monthly': 100000,
                'common_area_utilities_monthly': 30000,
                'tax_rate': 20
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        
        data = body['data']
        assert data['annual_loan_payment'] == 0
        assert data['monthly_loan_payment'] == 0
        # NOI should equal BTCF when there's no loan
        assert data['noi'] == data['btcf']

    def test_cash_flow_zero_vacancy(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with zero vacancy rate."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 40000000,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 0,
                'management_fee_rate': 6,
                'insurance_monthly': 50000,
                'maintenance_monthly': 100000,
                'common_area_utilities_monthly': 30000,
                'tax_rate': 20
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        
        breakdown = body['data']['breakdown']
        assert breakdown['vacancy_loss'] == 0

    def test_cash_flow_validation_error_missing_field(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with missing required field."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 40000000,
                # Missing loan_term_years
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 5
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'errors' in body

    def test_cash_flow_validation_error_invalid_value(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with invalid field value."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': -1000000,  # Invalid: negative value
                'loan_amount': 40000000,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 5
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'errors' in body

    def test_cash_flow_invalid_json(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with invalid JSON."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': 'invalid json{'
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'Invalid JSON' in body['error']['message']

    def test_cash_flow_empty_body(self, api_gateway_event, lambda_context):
        """Test cash flow calculation with empty body."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': '{}'
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 400
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'errors' in body

    def test_cash_flow_calculation_breakdown(self, api_gateway_event, lambda_context):
        """Test that breakdown contains all expected fields."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 40000000,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 5,
                'management_fee_rate': 6,
                'insurance_monthly': 50000,
                'maintenance_monthly': 100000,
                'common_area_utilities_monthly': 30000,
                'tax_rate': 20
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        breakdown = body['data']['breakdown']
        
        # Verify breakdown contains all expected fields
        expected_fields = [
            'total_monthly_rent',
            'vacancy_loss',
            'effective_monthly_rent',
            'management_fee',
            'insurance',
            'maintenance',
            'common_area_utilities',
            'monthly_noi',
            'annual_noi',
            'monthly_loan_payment',
            'annual_loan_payment',
            'monthly_btcf',
            'annual_btcf',
            'annual_tax',
            'monthly_atcf',
            'annual_atcf'
        ]
        
        for field in expected_fields:
            assert field in breakdown, f"Missing field: {field}"
            assert isinstance(breakdown[field], (int, float))

    def test_cash_flow_tax_calculation(self, api_gateway_event, lambda_context):
        """Test that tax is calculated correctly from BTCF."""
        # Arrange
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 40000000,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': 150000,
                'unit_count': 10,
                'vacancy_rate': 5,
                'management_fee_rate': 6,
                'insurance_monthly': 50000,
                'maintenance_monthly': 100000,
                'common_area_utilities_monthly': 30000,
                'tax_rate': 20
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        data = body['data']
        
        # Verify tax calculation: tax = BTCF * tax_rate
        expected_tax = data['btcf'] * 0.20
        assert abs(data['annual_tax'] - expected_tax) < 0.01
        
        # Verify ATCF = BTCF - tax
        expected_atcf = data['btcf'] - data['annual_tax']
        assert abs(data['atcf'] - expected_atcf) < 0.01

    def test_cash_flow_noi_calculation(self, api_gateway_event, lambda_context):
        """Test that NOI is calculated correctly."""
        # Arrange
        monthly_rent = 150000
        unit_count = 10
        vacancy_rate = 5
        management_fee_rate = 6
        insurance = 50000
        maintenance = 100000
        utilities = 30000
        
        event = {
            **api_gateway_event,
            'httpMethod': 'POST',
            'body': json.dumps({
                'property_price': 50000000,
                'loan_amount': 40000000,
                'loan_term_years': 30,
                'interest_rate': 2.5,
                'monthly_rent': monthly_rent,
                'unit_count': unit_count,
                'vacancy_rate': vacancy_rate,
                'management_fee_rate': management_fee_rate,
                'insurance_monthly': insurance,
                'maintenance_monthly': maintenance,
                'common_area_utilities_monthly': utilities,
                'tax_rate': 20
            })
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        breakdown = body['data']['breakdown']
        
        # Manual calculation
        total_rent = monthly_rent * unit_count
        effective_rent = total_rent * (1 - vacancy_rate / 100)
        management_fee = effective_rent * (management_fee_rate / 100)
        expected_noi = effective_rent - management_fee - insurance - maintenance - utilities
        
        assert abs(breakdown['monthly_noi'] - expected_noi) < 0.01

