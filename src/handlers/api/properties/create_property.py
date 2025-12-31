import os
import json
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from botocore.exceptions import ClientError
from pydantic import ValidationError
from shared.logging.logger import get_logger
from shared.database.connection import get_db_connection
from shared.database.models import Property, PropertyCreate
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
    Create property endpoint handler.
    
    Expected body:
    {
        "address": "123 Main St",
        "price": 500000,
        "location": "San Francisco",
        "property_type": "house",
        "bedrooms": 3,
        "bathrooms": 2.5,
        "square_feet": 1500,
        "description": "Beautiful house...",
        "status": "active"  # optional, defaults to "active"
    }
    
    Returns:
        API Gateway response with created property
    """
    try:
        logger.info("Create property requested", extra={"event": event})
        
        # Add custom metrics
        metrics.add_metric(name="CreatePropertyRequests", unit=MetricUnit.Count, value=1)
        
        # Get table name from environment
        table_name = os.environ.get('PROPERTIES_TABLE_NAME')
        if not table_name:
            logger.error("PROPERTIES_TABLE_NAME not set")
            return APIResponse.internal_error("Configuration error")
        
        # Parse request body
        try:
            if not event.get('body'):
                return APIResponse.validation_error("Request body is required")
            
            body = json.loads(event['body'])
            logger.info("Request body parsed", extra={"body_keys": list(body.keys())})
            
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in request body", extra={"error": str(e)})
            return APIResponse.validation_error("Invalid JSON format")
        
        # Validate request data
        try:
            property_create = PropertyCreate(**body)
            logger.info("Property data validated", extra={"property_data": property_create.dict()})
            
        except ValidationError as e:
            logger.error("Property validation failed", extra={"errors": e.errors()})
            error_messages = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                message = error['msg']
                error_messages.append(f"{field}: {message}")
            
            return APIResponse.validation_error(f"Validation errors: {'; '.join(error_messages)}")
        
        # Create property with system fields
        property_obj = Property.create_new(property_create)
        
        # Get database connection
        db_connection = get_db_connection()
        table = db_connection.get_table(table_name)
        
        # Check if property with same address already exists (optional business logic)
        try:
            # This is a simple check - in production you might want more sophisticated duplicate detection
            existing_response = table.scan(
                FilterExpression='address = :address',
                ExpressionAttributeValues={':address': property_obj.address},
                Limit=1
            )
            
            if existing_response.get('Items'):
                logger.warning("Property with same address already exists", extra={
                    "address": property_obj.address,
                    "existing_id": existing_response['Items'][0].get('id')
                })
                return APIResponse.validation_error("Property with this address already exists")
            
        except ClientError as e:
            # Log but don't fail the creation - duplicate check is nice-to-have
            logger.warning("Failed to check for duplicates", extra={"error": str(e)})
        
        # Save to DynamoDB
        try:
            item = property_obj.to_dynamodb_item()
            table.put_item(Item=item)
            
            logger.info("Property created successfully", extra={
                "property_id": property_obj.id,
                "address": property_obj.address,
                "price": float(property_obj.price)
            })
            
            metrics.add_metric(name="PropertiesCreated", unit=MetricUnit.Count, value=1)
            metrics.add_metric(
                name="PropertyPrice", 
                unit=MetricUnit.None, 
                value=float(property_obj.price)
            )
            
            # Return created property
            return APIResponse.success(property_obj.dict(), status_code=201)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error("DynamoDB error during property creation", extra={
                "error_code": error_code,
                "error": str(e),
                "property_id": property_obj.id
            })
            
            if error_code == 'ConditionalCheckFailedException':
                return APIResponse.validation_error("Property already exists")
            elif error_code == 'ResourceNotFoundException':
                return APIResponse.error("Properties table not found", 503, "SERVICE_UNAVAILABLE")
            else:
                metrics.add_metric(name="CreatePropertyDynamoDBErrors", unit=MetricUnit.Count, value=1)
                return APIResponse.internal_error("Failed to save property")
    
    except Exception as e:
        logger.error("Unexpected error in create_property", extra={
            "error": str(e),
            "event": event
        })
        metrics.add_metric(name="CreatePropertyErrors", unit=MetricUnit.Count, value=1)
        
        return APIResponse.internal_error("Failed to create property")