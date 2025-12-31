import os
import pytest
import boto3
from moto import mock_dynamodb
from decimal import Decimal

# Set test environment variables
os.environ['ENVIRONMENT'] = 'test'
os.environ['REGION'] = 'us-east-1'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['PROPERTIES_TABLE_NAME'] = 'test-real-estate-observability-properties'
os.environ['DYNAMODB_TABLE_PREFIX'] = 'test-real-estate-observability'

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture(scope='function')
def dynamodb_table(aws_credentials):
    """Create a mock DynamoDB table for testing."""
    with mock_dynamodb():
        # Create DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create properties table
        table = dynamodb.create_table(
            TableName=os.environ['PROPERTIES_TABLE_NAME'],
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'created_at',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'status',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'updated_at',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'location',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'price',
                    'AttributeType': 'N'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'StatusIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'status',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'updated_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                },
                {
                    'IndexName': 'LocationIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'location',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'price',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ]
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        
        yield table

@pytest.fixture
def sample_property_data():
    """Sample property data for testing."""
    return {
        'address': '123 Test Street',
        'price': Decimal('500000'),
        'location': 'Test City',
        'property_type': 'house',
        'bedrooms': 3,
        'bathrooms': Decimal('2.5'),
        'square_feet': 1500,
        'description': 'A beautiful test property',
        'status': 'active'
    }

@pytest.fixture
def api_gateway_event():
    """Sample API Gateway event for testing."""
    return {
        'httpMethod': 'GET',
        'path': '/properties',
        'headers': {
            'Content-Type': 'application/json'
        },
        'queryStringParameters': None,
        'body': None,
        'requestContext': {
            'requestId': 'test-request-id',
            'stage': 'test'
        }
    }

@pytest.fixture
def lambda_context():
    """Mock Lambda context for testing."""
    class MockContext:
        def __init__(self):
            self.function_name = 'test-function'
            self.function_version = '$LATEST'
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
            self.memory_limit_in_mb = 128
            self.remaining_time_in_millis = lambda: 30000
            self.aws_request_id = 'test-request-id'
    
    return MockContext()