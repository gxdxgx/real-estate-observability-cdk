import os
from typing import Dict, Any, List, Optional
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from botocore.exceptions import ClientError
from shared.logging.logger import get_logger
from shared.database.connection import get_db_connection
from shared.database.models import Property
from handlers.api.common.response import APIResponse

# Initialize AWS Lambda Powertools
logger = get_logger()
tracer = Tracer()
metrics = Metrics()

@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get properties endpoint handler.
    
    Query parameters:
        - status: Filter by property status
        - location: Filter by location
        - limit: Maximum number of properties to return (default: 50)
        - last_key: For pagination (base64 encoded)
    
    Returns:
        API Gateway response with list of properties
    """
    try:
        logger.info("Get properties requested", extra={"event": event})
        
        # Add custom metrics
        metrics.add_metric(name="GetPropertiesRequests", unit=MetricUnit.Count, value=1)
        
        # Get table name from environment
        table_name = os.environ.get('PROPERTIES_TABLE_NAME')
        if not table_name:
            logger.error("PROPERTIES_TABLE_NAME not set")
            return APIResponse.internal_error("Configuration error")
        
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        status_filter = query_params.get('status')
        location_filter = query_params.get('location')
        limit = min(int(query_params.get('limit', 50)), 100)  # Max 100 items
        
        logger.info("Query parameters", extra={
            "status_filter": status_filter,
            "location_filter": location_filter,
            "limit": limit
        })
        
        # Get database connection
        db_connection = get_db_connection()
        table = db_connection.get_table(table_name)
        
        properties = []
        
        if status_filter:
            # Query by status using GSI
            response = table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status_filter},
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            items = response.get('Items', [])
            
        elif location_filter:
            # Query by location using GSI
            response = table.query(
                IndexName='LocationIndex',
                KeyConditionExpression='#location = :location',
                ExpressionAttributeNames={'#location': 'location'},
                ExpressionAttributeValues={':location': location_filter},
                Limit=limit,
                ScanIndexForward=False  # Highest price first
            )
            items = response.get('Items', [])
            
        else:
            # Scan all properties (not recommended for large datasets)
            response = table.scan(
                Limit=limit,
                ProjectionExpression='id, address, price, #location, property_type, bedrooms, bathrooms, square_feet, #status, created_at, updated_at',
                ExpressionAttributeNames={
                    '#location': 'location',
                    '#status': 'status'
                }
            )
            items = response.get('Items', [])
        
        # Convert DynamoDB items to Property models
        for item in items:
            try:
                property_obj = Property.from_dynamodb_item(item)
                properties.append(property_obj.dict())
            except Exception as e:
                logger.warning("Failed to parse property item", extra={
                    "item_id": item.get('id', 'unknown'),
                    "error": str(e)
                })
                continue
        
        # Prepare response data
        response_data = {
            'properties': properties,
            'count': len(properties),
            'total_scanned': response.get('ScannedCount', len(properties)),
            'filters': {
                'status': status_filter,
                'location': location_filter,
                'limit': limit
            }
        }
        
        # Add pagination info if available
        if 'LastEvaluatedKey' in response:
            response_data['pagination'] = {
                'has_more': True,
                'last_key': response['LastEvaluatedKey']
            }
        
        logger.info("Properties retrieved successfully", extra={
            "properties_count": len(properties),
            "total_scanned": response.get('ScannedCount', len(properties))
        })
        
        metrics.add_metric(name="PropertiesRetrieved", unit=MetricUnit.Count, value=len(properties))
        
        return APIResponse.success(response_data)
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error("DynamoDB error", extra={"error_code": error_code, "error": str(e)})
        
        if error_code == 'ResourceNotFoundException':
            return APIResponse.error("Properties table not found", 503, "SERVICE_UNAVAILABLE")
        else:
            metrics.add_metric(name="GetPropertiesDynamoDBErrors", unit=MetricUnit.Count, value=1)
            return APIResponse.internal_error("Database error")
    
    except ValueError as e:
        logger.error("Validation error", extra={"error": str(e)})
        return APIResponse.validation_error(str(e))
    
    except Exception as e:
        logger.error("Unexpected error in get_properties", extra={"error": str(e)})
        metrics.add_metric(name="GetPropertiesErrors", unit=MetricUnit.Count, value=1)
        
        return APIResponse.internal_error("Failed to retrieve properties")