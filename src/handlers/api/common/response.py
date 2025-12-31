from typing import Dict, Any, Optional
from aws_lambda_powertools.event_handler.api_gateway import Response
from shared.utils.helpers import create_response, create_error_response

class APIResponse:
    """Standardized API response helper."""
    
    @staticmethod
    def success(data: Any, status_code: int = 200, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a successful response."""
        body = {
            'success': True,
            'data': data
        }
        return create_response(status_code, body, headers)
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create an error response."""
        return create_error_response(status_code, message, error_code)
    
    @staticmethod
    def not_found(resource: str = "Resource") -> Dict[str, Any]:
        """Create a 404 not found response."""
        return APIResponse.error(f"{resource} not found", 404, "NOT_FOUND")
    
    @staticmethod
    def validation_error(message: str) -> Dict[str, Any]:
        """Create a validation error response."""
        return APIResponse.error(message, 400, "VALIDATION_ERROR")
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> Dict[str, Any]:
        """Create a 500 internal server error response."""
        return APIResponse.error(message, 500, "INTERNAL_ERROR")