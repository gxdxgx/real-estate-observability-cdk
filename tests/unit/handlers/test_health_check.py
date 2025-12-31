import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from handlers.api.health.health_check import handler

class TestHealthCheck:
    """Test cases for health check handler."""

    def test_health_check_success(self, api_gateway_event, lambda_context, dynamodb_table):
        """Test successful health check."""
        # Arrange
        event = {
            **api_gateway_event,
            'path': '/health'
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['status'] == 'healthy'
        assert 'timestamp' in body['data']
        assert body['data']['service'] == 'real-estate-observability-api'
        assert body['data']['environment'] == 'test'

    def test_health_check_root_endpoint(self, api_gateway_event, lambda_context, dynamodb_table):
        """Test health check at root endpoint."""
        # Arrange
        event = {
            **api_gateway_event,
            'path': '/'
        }
        
        # Act
        response = handler(event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['status'] == 'healthy'
        assert body['data']['message'] == 'Welcome to Real Estate Observability API'
        assert 'endpoints' in body['data']
        assert body['data']['endpoints']['health'] == '/health'
        assert body['data']['endpoints']['properties'] == '/properties'

    def test_health_check_with_database(self, api_gateway_event, lambda_context, dynamodb_table):
        """Test health check with database connection."""
        # Act
        response = handler(api_gateway_event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert 'database' in body['data']
        assert body['data']['database']['status'] == 'healthy'
        assert body['data']['database']['table'] == os.environ['PROPERTIES_TABLE_NAME']

    @patch('handlers.api.health.health_check.get_db_connection')
    def test_health_check_database_error(self, mock_get_db_connection, api_gateway_event, lambda_context):
        """Test health check with database error."""
        # Arrange
        mock_connection = MagicMock()
        mock_connection.health_check.side_effect = Exception("Database error")
        mock_get_db_connection.return_value = mock_connection
        
        # Act
        response = handler(api_gateway_event, lambda_context)
        
        # Assert
        assert response['status_code'] == 200
        
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['data']['database']['status'] == 'error'
        assert body['data']['database']['error'] == 'Connection failed'

    @patch('handlers.api.health.health_check.get_current_timestamp')
    def test_health_check_handler_exception(self, mock_timestamp, api_gateway_event, lambda_context):
        """Test health check handler with unexpected exception."""
        # Arrange
        mock_timestamp.side_effect = Exception("Unexpected error")
        
        # Act
        response = handler(api_gateway_event, lambda_context)
        
        # Assert
        assert response['status_code'] == 500
        
        body = json.loads(response['body'])
        assert body['success'] is False
        assert 'error' in body
        assert body['error']['message'] == 'Health check failed'