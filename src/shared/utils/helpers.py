import json
import datetime
from typing import Any, Dict, Optional
from decimal import Decimal

def decimal_serializer(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create a standardized API Gateway response."""
    
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'status_code': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=decimal_serializer, ensure_ascii=False)
    }

def create_error_response(
    status_code: int,
    error_message: str,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    
    error_body = {
        'error': {
            'message': error_message,
            'timestamp': datetime.datetime.now().isoformat()
        }
    }
    
    if error_code:
        error_body['error']['code'] = error_code
    
    return create_response(status_code, error_body)

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.datetime.now().isoformat()

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """Validate that all required fields are present in the data."""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None