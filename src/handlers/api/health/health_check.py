import os
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from shared.logging.logger import get_logger
from shared.database.connection import get_db_connection
from shared.utils.helpers import get_current_timestamp
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
    Health check endpoint handler.
    
    Returns:
        API Gateway response with health status
    """
    try:
        logger.info("Health check requested", extra={"event": event})
        
        # Add custom metrics
        metrics.add_metric(name="HealthCheckRequests", unit=MetricUnit.Count, value=1)
        
        # Get environment info
        environment = os.environ.get('ENVIRONMENT', 'unknown')
        region = os.environ.get('REGION', 'unknown')
        
        # Basic health data
        health_data = {
            'status': 'healthy',
            'timestamp': get_current_timestamp(),
            'environment': environment,
            'region': region,
            'service': 'real-estate-observability-api'
        }
        
        # Check database connection if table name is available
        properties_table_name = os.environ.get('PROPERTIES_TABLE_NAME')
        if properties_table_name:
            try:
                db_connection = get_db_connection()
                db_healthy = db_connection.health_check(properties_table_name)
                health_data['database'] = {
                    'status': 'healthy' if db_healthy else 'unhealthy',
                    'table': properties_table_name
                }
                
                if not db_healthy:
                    metrics.add_metric(name="DatabaseHealthCheckFailed", unit=MetricUnit.Count, value=1)
                    logger.warning("Database health check failed", extra={"table": properties_table_name})
                    
            except Exception as e:
                logger.error("Database health check error", extra={"error": str(e)})
                health_data['database'] = {
                    'status': 'error',
                    'error': 'Connection failed'
                }
                metrics.add_metric(name="DatabaseHealthCheckError", unit=MetricUnit.Count, value=1)
        
        # Check if this is the root endpoint
        path = event.get('path', '')
        if path == '/':
            health_data['message'] = 'Welcome to Real Estate Observability API'
            health_data['endpoints'] = {
                'health': '/health',
                'properties': '/properties'
            }
        
        logger.info("Health check completed successfully", extra=health_data)
        
        return APIResponse.success(health_data)
        
    except Exception as e:
        logger.error("Health check failed", extra={"error": str(e)})
        metrics.add_metric(name="HealthCheckErrors", unit=MetricUnit.Count, value=1)
        
        return APIResponse.internal_error("Health check failed")